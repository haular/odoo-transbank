from odoo import fields, models

class PaymentToken(models.Model):
    _inherit = 'payment.token'

    # Transbank Oneclick specific fields
    transbank_tbk_user = fields.Char(
        string='Transbank TBK User',
        readonly=True,
        help='The unique user identifier provided by Transbank'
    )
    transbank_username = fields.Char(
        string='Transbank Username',
        readonly=True,
        help='The internal username used during registration'
    )
    transbank_card_type = fields.Char(
        string='Card Type',
        readonly=True,
    )
