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
        _logger.info("Webpay: entering form_feedback with data:\n%s", pprint.pformat(data))
        
        # Transbank sends 'token_ws' on success, or 'tbk_token' on abort.
        token = data.get('token_ws') or data.get('tbk_token')
        
        if not token:
            _logger.warning('Webpay: Received return without token.')
            return request.redirect('/payment/status')

        # We need to process the transaction feedback.
        # This calls '_handle_notification_data' on 'payment.transaction' model.
        request.env['payment.transaction'].sudo()._handle_notification_data('transbank', data)
        
        return request.redirect('/payment/status')
