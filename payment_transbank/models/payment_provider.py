from odoo import fields, models, _

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('transbank', 'Transbank')], ondelete={'transbank': 'set default'}
    )
    transbank_commerce_code = fields.Char(
        string='Commerce Code',
        required_if_provider='transbank',
        help='The commerce code provided by Transbank'
    )
    transbank_api_key = fields.Char(
        string='API Key',
        required_if_provider='transbank',
        groups='base.group_system',
        help='The API Key provided by Transbank'
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