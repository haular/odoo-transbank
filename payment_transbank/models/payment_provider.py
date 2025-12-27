from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('transbank', 'Transbank')], ondelete={'transbank': 'set default'}
    )

    # Webpay Plus Credentials
    transbank_commerce_code = fields.Char(
        string='Webpay Commerce Code',
        help='The commerce code provided by Transbank for Webpay Plus'
    )
    transbank_api_key = fields.Char(
        string='Webpay API Key',
        groups='base.group_system',
        help='The API Key provided by Transbank for Webpay Plus'
    )

    # Oneclick Mall Credentials
    transbank_oneclick_commerce_code = fields.Char(
        string='Oneclick Commerce Code',
        help='The commerce code provided by Transbank for Oneclick Mall'
    )
    transbank_oneclick_api_key = fields.Char(
        string='Oneclick API Key',
        groups='base.group_system',
        help='The API Key provided by Transbank for Oneclick Mall'
    )

    def _get_supported_currencies(self):
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'transbank':
            supported_currencies = supported_currencies.filtered(lambda c: c.name in ('CLP', 'USD'))
        return supported_currencies

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code == 'transbank':
            return ['webpay', 'oneclick']
        return default_codes

    def _get_transbank_options(self, method_code):
        """ Template method to be overridden by sub-modules (webpay, oneclick).
        :param str method_code: The code of the payment method ('webpay' or 'oneclick')
        :return: An instance of transbank.common.options.WebpayOptions or None for test mode.
        """
        self.ensure_one()
        return None
