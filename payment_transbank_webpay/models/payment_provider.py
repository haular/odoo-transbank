from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions

from odoo import models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    def _get_transbank_options(self, method_code):
        """ Override to provide Webpay Plus specific options. """
        res = super()._get_transbank_options(method_code)
        if self.code != 'transbank' or method_code != 'webpay':
            return res
        integration_type = IntegrationType.TEST
        if self.state == 'enabled':
            integration_type = IntegrationType.LIVE
        return WebpayOptions(
            self.transbank_commerce_code,
            self.transbank_api_key,
            integration_type
        )
