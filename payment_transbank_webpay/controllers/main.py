import pprint

from odoo import http
from odoo.http import request

from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.payment_transbank import const

_logger = get_payment_logger(__name__, const.SENSITIVE_KEYS)


class WebpayController(http.Controller):
    _return_url = '/payment/transbank/return'

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def transbank_return(self, reference=None, **data):
        """Handle the customer's return from Webpay.

        Webpay redirects by GET, except for an aborted payment in the integration environment
        (POST). The route is public, so the data is only trusted once matched to the transaction.
        """
        _logger.info('Handling redirection from Webpay for %s with data:\n%s', reference, pprint.pformat(data))
        tx_sudo = self.env['payment.transaction'].sudo()._search_by_reference('transbank', {'reference': reference})
        if tx_sudo and tx_sudo.state in ('draft', 'pending'):
            payment_data = tx_sudo._transbank_get_return_payment_data(data)
            if payment_data:
                tx_sudo._record(payment_data)
            else:
                _logger.warning('Ignored Webpay return data not matching transaction %s', tx_sudo.reference)
        return request.redirect('/payment/status')
