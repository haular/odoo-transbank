import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # Common Transbank fields
    transbank_payment_type_code = fields.Char(string='Transbank Payment Type', readonly=True)
    transbank_response_code = fields.Integer(string='Transbank Response Code', readonly=True)
    transbank_status = fields.Char(string='Transbank Status', readonly=True)
    transbank_authorization_code = fields.Char(string='Authorization Code', readonly=True)
    transbank_card_number = fields.Char(string='Card Last Digits', readonly=True)

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Find the transaction based on the notification data."""
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'transbank' or tx:
            return tx

        return self._search_by_reference(provider_code, notification_data)

    def _process_notification_data(self, notification_data):
        """Process the notification data and update the transaction."""
        super()._process_notification_data(notification_data)
        if self.provider_code != 'transbank':
            return

        self._apply_updates(notification_data)

    def _apply_updates(self, payment_data):
        """Placeholder for sub-modules to implement their specific logic."""
        return

    def _extract_amount_data(self, payment_data):
        if self.provider_code != 'transbank':
            return super()._extract_amount_data(payment_data)
        return None
