import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class TransbankController(http.Controller):
    _return_url = '/payment/transbank/return'
    _oneclick_confirm_url = '/payment/transbank/oneclick/confirm'

    @http.route(_return_url, type='http', auth='public', methods=['POST', 'GET'], csrf=False, save_session=False)
    def transbank_return(self, **data):
        """ Webpay Plus return point. """
        _logger.info("Transbank: entering form_feedback with data:\n%s", pprint.pformat(data))
        token = data.get('token_ws') or data.get('TBK_TOKEN') or data.get('tbk_token')
        
        if not token:
            _logger.warning('Transbank: Received return without token.')
            return request.redirect('/payment/status')

        request.env['payment.transaction'].sudo()._process('transbank', data)
        return request.redirect('/payment/status')

    @http.route(_oneclick_confirm_url, type='http', auth='public', methods=['POST', 'GET'], csrf=False, save_session=False)
    def transbank_oneclick_confirm(self, **data):
        """ Oneclick Mall inscription confirmation point. """
        _logger.info("Transbank Oneclick: entering confirmation with data:\n%s", pprint.pformat(data))
        token = data.get('token_ws') or data.get('TBK_TOKEN') or data.get('tbk_token')
        
        if not token:
            _logger.warning('Transbank Oneclick: Received confirmation without token.')
            return request.redirect('/payment/status')

        # Oneclick registration confirmation also uses the _process flow
        request.env['payment.transaction'].sudo()._process('transbank', data)
        return request.redirect('/payment/status')