import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WebpayController(http.Controller):
    _return_url = '/payment/transbank/return'

    @http.route(_return_url, type='http', auth='public', methods=['POST', 'GET'], csrf=False, save_session=False)
    def transbank_return(self, **data):
        """ Webpay Plus return point. """
        _logger.info("Webpay Plus: entering form_feedback with data:\n%s", pprint.pformat(data))
        token = data.get('token_ws') or data.get('TBK_TOKEN') or data.get('tbk_token')

        if not token:
            _logger.warning('Webpay Plus: Received return without token.')
            return request.redirect('/payment/status')

        request.env['payment.transaction'].sudo()._process('transbank', data)
        return request.redirect('/payment/status')
