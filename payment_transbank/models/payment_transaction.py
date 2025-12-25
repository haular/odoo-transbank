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

    def _get_transbank_tx_client(self):
        """ Helper to get the configured Transbank Transaction client. """
        if self.provider_id.state == 'enabled':
            # Production
            commerce_code = self.provider_id.transbank_commerce_code
            api_key = self.provider_id.transbank_api_key
            integration_type = IntegrationType.LIVE
        else:
            # Test / Disabled (Defaults to Integration for safety)
            commerce_code = IntegrationCommerceCodes.WEBPAY_PLUS
            api_key = IntegrationApiKeys.WEBPAY
            integration_type = IntegrationType.TEST
        
        return Transaction(WebpayOptions(commerce_code, api_key, integration_type))

    def _get_specific_rendering_values(self, processing_values):
        """ Create the transaction on Transbank and return the data for the redirect form. """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'transbank':
            return res

        # 1. Setup Transbank SDK
        tx = self._get_transbank_tx_client()
        
        # 2. Prepare Data
        buy_order = self.reference
        session_id = self.reference
        amount = self.amount
        
        base_url = self.provider_id.get_base_url()
        return_url = urls.url_join(base_url, '/payment/transbank/return')

        # 3. Call Transbank API
        try:
            response = tx.create(
                buy_order=buy_order,
                session_id=session_id,
                amount=amount,
                return_url=return_url
            )
            _logger.info("Transbank: Transaction created for ref %s. Token: %s", self.reference, response.get('token'))
        except TransbankError as e:
            _logger.error("Transbank: Error creating transaction for ref %s: %s", self.reference, str(e))
            raise ValidationError(_("Could not initiate the payment with Transbank. %s", e.message))

        # IMPORTANT: Save the token as provider_reference so we can find the tx later
        self.provider_reference = response.get('token')

        rendering_values = {
            'api_url': response.get('url'),
            'token_ws': response.get('token'),
            'provider_code': self.provider_code,
        }
        return rendering_values

    @api.model
    def _search_by_reference(self, provider_code, payment_data):
        """ Override to find the transaction by token_ws or TBK_TOKEN. """
        if provider_code != 'transbank':
            return super()._search_by_reference(provider_code, payment_data)

        # 1. Look for the token in the incoming data
        token = payment_data.get('token_ws') or payment_data.get('TBK_TOKEN') or payment_data.get('tbk_token')
        
        if not token:
            _logger.warning("Transbank: No token found in notification data.")
            return self.env['payment.transaction']

        # 2. Search for the transaction that has this token as provider_reference
        tx = self.search([
            ('provider_reference', '=', token),
            ('provider_code', '=', 'transbank')
        ], limit=1)
        
        if not tx:
            _logger.warning("Transbank: No transaction found for token %s", token)
        
        return tx

    def _extract_amount_data(self, payment_data):
        """ Override to skip Odoo's default amount validation, as we validate via commit(). """
        if self.provider_code != 'transbank':
            return super()._extract_amount_data(payment_data)
        return None

    def _apply_updates(self, payment_data):
        """ Process the transaction based on Transbank response. """
        if self.provider_code != 'transbank':
            return super()._apply_updates(payment_data)

        _logger.info("Transbank: Processing updates with keys: %s", list(payment_data.keys()))

        token_ws = payment_data.get('token_ws')
        tbk_token = payment_data.get('TBK_TOKEN') or payment_data.get('tbk_token')

        # === CASE 1: ABORT / ERROR ===
        # If we have TBK_TOKEN and NO token_ws, it means the user clicked "Anular" or there was an error.
        # Transbank docs: "En caso de que el tarjetahabiente haya declinado... recibirás TBK_TOKEN"
        if tbk_token and not token_ws:
            _logger.warning("Transbank: Transaction aborted by user or error. TBK_TOKEN: %s", tbk_token)
            self._set_canceled(state_message=_("Payment aborted by user on Transbank."))
            return

        # === CASE 2: SUCCESS FLOW ===
        if not token_ws:
            # Should not happen if _search_by_reference worked, but safety first
            _logger.error("Transbank: Logic error. Reached _apply_updates without token_ws.")
            self._set_error("No Webpay Token found.")
            return

        # We must COMMIT the transaction with Transbank to get the real status.
        tx_client = self._get_transbank_tx_client()
        
        try:
            _logger.info("Transbank: Committing token %s", token_ws)
            response = tx_client.commit(token_ws)
            _logger.info("Transbank: Commit response:\n%s", pprint.pformat(response))
        except TransbankError as e:
            _logger.error("Transbank: Commit failed for token %s: %s", token_ws, str(e))
            # If commit fails, we try to ask for status (idempotency) just in case it was already committed
            try:
                response = tx_client.status(token_ws)
                _logger.info("Transbank: Recovered status:\n%s", pprint.pformat(response))
            except Exception:
                self._set_error(_("An error occurred while validating the transaction with Transbank."))
                return

        # Analyze status code (response_code 0 = Authorized)
        if response.get('response_code') == 0:
            if response.get('status') == 'AUTHORIZED':
                self._set_done()
            else:
                _logger.warning("Transbank: Status is %s (not AUTHORIZED)", response.get('status'))
                self._set_error(_("Transaction rejected by Transbank. Status: %s", response.get('status')))
        else:
            _logger.warning("Transbank: Rejected. Response code: %s", response.get('response_code'))
            self._set_error(_("Transaction rejected by Transbank."))