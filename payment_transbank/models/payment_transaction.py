import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # Common Transbank fields
    transbank_payment_type_code = fields.Char(string="Transbank Payment Type", readonly=True)
    transbank_response_code = fields.Integer(string="Transbank Response Code", readonly=True)
    transbank_status = fields.Char(string="Transbank Status", readonly=True)
    transbank_authorization_code = fields.Char(string="Authorization Code", readonly=True)
    transbank_card_number = fields.Char(string="Card Last Digits", readonly=True)

    def _extract_amount_data(self, payment_data):
        if self.provider_code != 'transbank':
            return super()._extract_amount_data(payment_data)
        return None
