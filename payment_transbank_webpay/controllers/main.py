import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WebpayController(http.Controller):
    _return_url = '/payment/transbank/return'

    @http.route(_return_url, type='http', auth='public', methods=['POST', 'GET'], csrf=False, save_session=False)
    def transbank_return(self, reference=None, **data):
        _logger.info('Webpay: confirmation callback with data:\n%s', pprint.pformat(data))
        tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference('transbank', {'reference': reference})
        if not tx_sudo:
            _logger.warning('Webpay: No transaction found for reference %s', reference)
            return request.redirect('/shop/cart')
        token_ws = data.get('token_ws')
        tbk_token = data.get('TBK_TOKEN') or data.get('tbk_token')
        if not token_ws and tbk_token:
            tx_sudo._set_canceled(state_message='The user cancelled the Webpay payment.')
            return request.redirect('/payment/status')
        elif not token_ws and not tbk_token:
            tx_sudo._set_error('No token received from Transbank. Possible timeout.')
            return request.redirect('/payment/status')
        elif tx_sudo.provider_reference != token_ws:
            _logger.warning(
                'Webpay: Token mismatch for tx %s. Expected %s, got %s',
                tx_sudo.reference,
                tx_sudo.provider_reference,
                token_ws,
            )
            tx_sudo._set_error('Validation error: the received token does not match.')
            return request.redirect('/payment/status')
        tx_sudo._process('transbank', data)
        return request.redirect('/payment/status')
