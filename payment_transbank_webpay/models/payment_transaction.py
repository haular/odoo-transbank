import logging

from transbank.error.transbank_error import TransbankError
from transbank.webpay.webpay_plus.transaction import Transaction as WebpayPlusTransaction
from werkzeug import urls

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'transbank' or self.payment_method_code != 'webpay':
            return res

        options = self.provider_id._get_transbank_options('webpay')
        tx = WebpayPlusTransaction(options)
        return_url = urls.url_join(self.provider_id.get_base_url(), '/payment/transbank/return')
        amount = self.amount if self.state == 'enabled' else round(self.amount)

        try:
            response = tx.create(
                buy_order=self.reference,
                session_id=self.reference,
                amount=amount,
                return_url=return_url
            )
            self.provider_reference = response.get('token')
            return {
                'api_url': response.get('url'),
                'token_ws': response.get('token'),
                'provider_code': self.provider_code,
            }
        except TransbankError as e:
            _logger.error("Webpay Plus: Error creating transaction: %s", str(e))
            raise ValidationError(_("Could not initiate Webpay payment."))

    def _apply_updates(self, payment_data):
        if self.provider_code != 'transbank' or self.payment_method_code != 'webpay':
            return super()._apply_updates(payment_data)

        token_ws = payment_data.get('token_ws')
        if not token_ws:
            return super()._apply_updates(payment_data)

        options = self.provider_id._get_transbank_options('webpay')
        tx_client = WebpayPlusTransaction(options)

        try:
            response = tx_client.commit(token_ws)
            # Save technical data
            self.write({
                'transbank_response_code': response.get('response_code'),
                'transbank_status': response.get('status'),
                'transbank_authorization_code': response.get('authorization_code'),
                'transbank_card_number': response.get('card_detail', {}).get('card_number'),
            })

            if response.get('response_code') == 0 and response.get('status') == 'AUTHORIZED':
                self._set_done()
            else:
                self._set_error(_("Webpay rejected the payment."))
        except Exception as e:
            self._set_error(str(e))
