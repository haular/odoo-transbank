import logging
import pprint
from werkzeug import urls

from odoo import _, api, models
from odoo.exceptions import ValidationError

from transbank.error.transbank_error import TransbankError
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_type import IntegrationType

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_transbank_transaction(self):
        commerce_code = IntegrationCommerceCodes.WEBPAY_PLUS
        api_key = IntegrationApiKeys.WEBPAY
        integration_type = IntegrationType.TEST
        if self.provider_id.state == 'enabled':
            # Production
            commerce_code = self.provider_id.transbank_commerce_code
            api_key = self.provider_id.transbank_api_key
            integration_type = IntegrationType.LIVE
        return Transaction(WebpayOptions(commerce_code, api_key, integration_type))

    def _get_specific_rendering_values(self, processing_values):
        """ Create the transaction on Transbank and return the data for the redirect form. """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'transbank':
            return res

        # 1. Setup Transbank SDK
        tbk_transaction = self._get_transbank_transaction()
        
        # 2. Prepare Data
        buy_order = self.reference
        session_id = self.reference
        amount = self.amount
        
        base_url = self.provider_id.get_base_url()
        return_url = urls.url_join(base_url, '/payment/transbank/return')

        # 3. Call Transbank API
        try:
            response = tbk_transaction.create(
                buy_order=buy_order,
                session_id=session_id,
                amount=amount,
                return_url=return_url
            )
            _logger.info("Transbank: Transaction created for ref %s. Token: %s", self.reference, response.get('token'))
        except TransbankError as e:
            _logger.error("Transbank: Error creating transaction for ref %s: %s", self.reference, str(e))
            raise ValidationError(_("Could not initiate the payment with Transbank. %s", e.message))

        # IMPORTANT: Save the token as provider_reference so we can find the tbk_transaction later
        self.provider_reference = response.get('token')

        rendering_values = {
            'api_url': response.get('url'),
            'token_ws': response.get('token'),
            'provider_code': self.provider_code,
        }
        return rendering_values

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Find the transaction based on the token sent back by Transbank. """
        if provider_code != 'transbank':
            return super()._get_tx_from_notification_data(provider_code, notification_data)

        # Transbank sends 'token_ws' (success) or 'tbk_token' (abort)
        token = notification_data.get('token_ws') or notification_data.get('tbk_token')
        
        if not token:
            raise ValidationError("Transbank: No token found in notification data.")

        transaction_id = self.search([('provider_reference', '=', token), ('provider_code', '=', 'transbank')], limit=1)
        if not transaction_id:
            raise ValidationError("Transbank: No transaction found for token %s" % token)
        return transaction_id

    def _process_notification_data(self, notification_data):
        """ Process the transaction after finding it. Confirm with Transbank. """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'transbank':
            return

        token = notification_data.get('token_ws')
        tbk_token = notification_data.get('tbk_token')

        # Case 1: Aborted by user (tbk_token is present, token_ws is usually missing or empty)
        if tbk_token and not token:
            _logger.warning("Transbank: Transaction aborted by user. Token: %s", tbk_token)
            self._set_canceled()
            return

        # Case 2: Success flow (token_ws is present)
        # We must COMMIT the transaction with Transbank to get the real status.
        tbk_transaction = self._get_transbank_transaction()
        
        try:
            response = tbk_transaction.commit(token)
            _logger.info("Transbank: Commit response for token %s:\n%s", token, pprint.pformat(response))
        except TransbankError as e:
            # If commit fails (e.g. timeout, double commit), we check status or fail
            _logger.error("Transbank: Commit failed for token %s: %s", token, str(e))
            # Try to get status to be sure, or fail
            try:
                status_response = tbk_transaction.status(token)
                response = status_response
            except Exception:
                self._set_error(_("An error occurred while validating the transaction with Transbank."))
                return

        # Analyze status code
        # response_code 0 means Authorized.
        if response.get('response_code') == 0:
            if response.get('status') == 'AUTHORIZED':
                self._set_done()
            else:
                _logger.warning("Transbank: Transaction status is %s (not AUTHORIZED)", response.get('status'))
                self._set_error(_("Transaction rejected by Transbank. Status: %s", response.get('status')))
        else:
            _logger.warning("Transbank: Transaction rejected. Response code: %s", response.get('response_code'))
            self._set_error(_("Transaction rejected by Transbank."))