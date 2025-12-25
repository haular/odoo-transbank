import logging
from werkzeug import urls

from odoo import _, models
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

    def _get_specific_rendering_values(self, processing_values):
        """ Create the transaction on Transbank and return the data for the redirect form. """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'transbank':
            return res

        # Test / Disabled (Defaults to Integration for safety)
        commerce_code = IntegrationCommerceCodes.WEBPAY_PLUS
        api_key = IntegrationApiKeys.WEBPAY
        integration_type = IntegrationType.TEST
        if self.provider_id.state == 'enabled':
            # Production
            commerce_code = self.provider_id.transbank_commerce_code
            api_key = self.provider_id.transbank_api_key
            integration_type = IntegrationType.LIVE

        # Configure the Transaction Request
        tx = Transaction(WebpayOptions(commerce_code, api_key, integration_type))
        
        # 2. Prepare Data
        buy_order = self.reference  # Odoo's unique reference (e.g., tx-2023-001)
        session_id = self.reference
        amount = self.amount
        
        # Build the return URL (The controller we will create next)
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

        # 4. Pass Data to the Redirect Form
        # 'api_url' is where the form will POST to
        # 'token_ws' is the token required by Webpay
        rendering_values = {
            'api_url': response.get('url'),
            'token_ws': response.get('token'),
            'provider_code': self.provider_code,
        }
        return rendering_values
