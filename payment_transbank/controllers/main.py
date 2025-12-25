import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class TransbankController(http.Controller):
    _return_url = '/payment/transbank/return'

    @http.route(_return_url, type='http', auth='public', methods=['POST', 'GET'], csrf=False, save_session=False)
    def transbank_return(self, **data):
        """ Webpay Plus return point. """
        _logger.info("Transbank: entering form_feedback with data:\n%s", pprint.pformat(data))
        
        # 1. Extract Token
        # Transbank flow: 'token_ws' (Success)
        # Abort flow: 'TBK_TOKEN' (Abort/Error) - sent via POST (Int) or GET (Prod)
        token_ws = data.get('token_ws')
        tbk_token = data.get('TBK_TOKEN') or data.get('tbk_token') # Handle both cases just to be safe

        # 2. Validation
        if not token_ws and not tbk_token:
            _logger.warning('Transbank: Received return without token_ws or TBK_TOKEN.')
            return request.redirect('/payment/status')

        # 3. Process
        # We pass the data as-is. The model will decide if it's a success or abort based on keys.
        request.env['payment.transaction'].sudo()._process('transbank', data)
        
        return request.redirect('/payment/status')
