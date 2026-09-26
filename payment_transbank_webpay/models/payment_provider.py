from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions

from odoo import fields, models

from odoo.addons.payment_transbank import const


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    transbank_webpay_commerce_code = fields.Char(
        string='Webpay Commerce Code', help='The commerce code provided by Transbank for Webpay Plus'
    )
    transbank_webpay_api_key = fields.Char(
        string='Webpay API Key', groups='base.group_system', help='The API Key provided by Transbank for Webpay Plus'
    )

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code == 'transbank':
            return default_codes | {'webpay'}
        return default_codes

    def _get_transbank_options(self, method_code):
        res = super()._get_transbank_options(method_code)
        if self.code != 'transbank' or method_code != 'webpay':
            return res
        # Never log these options: their repr() prints the API key.
        if self.is_live:
            return WebpayOptions(
                self.transbank_webpay_commerce_code,
                self.transbank_webpay_api_key,
                IntegrationType.LIVE,
                timeout=const.API_TIMEOUT,
            )
        return WebpayOptions(
            self.transbank_webpay_commerce_code or IntegrationCommerceCodes.WEBPAY_PLUS,
            self.transbank_webpay_api_key or IntegrationApiKeys.WEBPAY,
            IntegrationType.TEST,
            timeout=const.API_TIMEOUT,
        )
