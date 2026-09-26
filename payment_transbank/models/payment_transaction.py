from odoo import api, fields, models

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_transbank import const


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    transbank_payment_type_code = fields.Char(string='Transbank Payment Type', readonly=True)
    transbank_response_code = fields.Integer(string='Transbank Response Code', readonly=True)
    transbank_status = fields.Char(string='Transbank Status', readonly=True)
    transbank_authorization_code = fields.Char(string='Authorization Code', readonly=True)
    transbank_card_number = fields.Char(string='Card Last Digits', readonly=True)

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator='-', **kwargs):
        """Keep the reference usable as Transbank buy_order (max 26 chars, restricted charset)."""
        reference = super()._compute_reference(provider_code, prefix=prefix, separator=separator, **kwargs)
        if provider_code != 'transbank' or self._transbank_is_valid_buy_order(reference):
            return reference
        prefix = payment_utils.singularize_reference_prefix(prefix='TB', separator=separator)
        return super()._compute_reference(provider_code, prefix=prefix, separator=separator, **kwargs)

    @api.model
    def _transbank_is_valid_buy_order(self, reference):
        return len(reference) <= const.BUY_ORDER_MAX_LENGTH and bool(const.BUY_ORDER_PATTERN.match(reference))

    def _extract_amount_data(self, payment_data):
        if self.provider_code != 'transbank':
            return super()._extract_amount_data(payment_data)
        if 'amount' not in payment_data:  # Nothing was charged (aborted, timed out, ...).
            return None
        # The Transbank response has no currency field: the commerce code fixes it.
        return {'amount': payment_data['amount'], 'currency_code': self.currency_id.name}
