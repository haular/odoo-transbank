import logging
import pprint
from werkzeug import urls

from odoo import _, api, models
from odoo.exceptions import ValidationError

from transbank.error.transbank_error import TransbankError
from transbank.webpay.webpay_plus.transaction import Transaction as WebpayPlusTransaction
from transbank.webpay.oneclick.mall_inscription import MallInscription
from transbank.webpay.oneclick.mall_transaction import MallTransaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_type import IntegrationType

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_transbank_options(self, product='webpay'):
        """ Helper to get the configured Transbank Options for a specific product. """
        if self.provider_id.state == 'enabled':
            # Production
            if product == 'oneclick':
                commerce_code = self.provider_id.transbank_oneclick_commerce_code
                api_key = self.provider_id.transbank_oneclick_api_key
            else:
                commerce_code = self.provider_id.transbank_commerce_code
                api_key = self.provider_id.transbank_api_key
            integration_type = IntegrationType.LIVE
        else:
            # Test / Disabled
            if product == 'oneclick':
                commerce_code = IntegrationCommerceCodes.ONECLICK_MALL
            else:
                commerce_code = IntegrationCommerceCodes.WEBPAY_PLUS
            api_key = IntegrationApiKeys.WEBPAY
            integration_type = IntegrationType.TEST
        
        return WebpayOptions(commerce_code, api_key, integration_type)

    def _get_specific_rendering_values(self, processing_values):
        """ Create the transaction or inscription on Transbank. """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'transbank':
            return res

        base_url = self.provider_id.get_base_url()

        # CASE 1: Webpay Plus
        if self.payment_method_code == 'webpay':
            tx = WebpayPlusTransaction(self._get_transbank_options('webpay'))
            return_url = urls.url_join(base_url, '/payment/transbank/return')
            
            try:
                response = tx.create(
                    buy_order=self.reference,
                    session_id=self.reference,
                    amount=self.amount,
                    return_url=return_url
                )
                self.provider_reference = response.get('token')
                return {
                    'api_url': response.get('url'),
                    'token_ws': response.get('token'),
                    'provider_code': self.provider_code,
                }
            except TransbankError as e:
                _logger.error("Transbank Webpay: Error creating transaction: %s", str(e))
                raise ValidationError(_("Could not initiate Webpay payment. %s", e.message))

        # CASE 2: Oneclick Mall Inscription (Registration flow)
        # We trigger this if the user selects Oneclick and doesn't have a token,
        # or if it is a explicit validation operation.
        elif self.payment_method_code == 'oneclick':
            ins = MallInscription(self._get_transbank_options('oneclick'))
            return_url = urls.url_join(base_url, '/payment/transbank/oneclick/confirm')
            
            # Username must be unique and consistent for this partner
            username = f"odoo_user_{self.partner_id.id}"
            email = self.partner_email or 'no-email@odoo.com'
            
            try:
                _logger.info("Transbank Oneclick: Starting inscription for user %s", username)
                response = ins.start(
                    username=username,
                    email=email,
                    response_url=return_url
                )
                self.provider_reference = response.get('token')
                return {
                    'api_url': response.get('url_webpay'),
                    'token_ws': response.get('token'),
                    'provider_code': self.provider_code,
                    'is_oneclick_registration': True,
                }
            except TransbankError as e:
                _logger.error("Transbank Oneclick: Error starting inscription: %s", str(e))
                raise ValidationError(_("Could not initiate Oneclick registration. %s", e.message))

        return res

    @api.model
    def _search_by_reference(self, provider_code, payment_data):
        if provider_code != 'transbank':
            return super()._search_by_reference(provider_code, payment_data)

        # token_ws for success, TBK_TOKEN for success(oneclick) or abort
        token = payment_data.get('token_ws') or payment_data.get('TBK_TOKEN') or payment_data.get('tbk_token')
        
        if not token:
            return self.env['payment.transaction']

        tx = self.search([
            ('provider_reference', '=', token),
            ('provider_code', '=', 'transbank')
        ], limit=1)
        return tx

    def _extract_amount_data(self, payment_data):
        if self.provider_code != 'transbank':
            return super()._extract_amount_data(payment_data)
        return None

    def _apply_updates(self, payment_data):
        if self.provider_code != 'transbank':
            return super()._apply_updates(payment_data)

        token_ws = payment_data.get('token_ws')
        tbk_token = payment_data.get('TBK_TOKEN') or payment_data.get('tbk_token')

        # 1. Handle Abort
        if tbk_token and not token_ws:
            self._set_canceled(state_message=_("Payment aborted by user on Transbank."))
            return

        # 2. Handle Webpay Plus Success
        if self.payment_method_code == 'webpay':
            tx_client = WebpayPlusTransaction(self._get_transbank_options('webpay'))
            try:
                response = tx_client.commit(token_ws)
                if response.get('response_code') == 0 and response.get('status') == 'AUTHORIZED':
                    self._set_done()
                else:
                    self._set_error(_("Webpay rejected. Status: %s", response.get('status')))
            except Exception as e:
                self._set_error(str(e))

        # 3. Handle Oneclick Inscription Confirmation
        elif self.payment_method_code == 'oneclick':
            # Note: In Oneclick registration, Transbank sends TBK_TOKEN on success
            # even if it was called via token_ws in some SDK versions, 
            # but usually 'finish' expects the token that came back.
            token = token_ws or tbk_token
            ins = MallInscription(self._get_transbank_options('oneclick'))
            try:
                _logger.info("Transbank Oneclick: Finishing inscription for token %s", token)
                response = ins.finish(token)
                if response.get('response_code') == 0:
                    self._transbank_oneclick_create_token(response)
                    self._set_done()
                else:
                    self._set_error(_("Oneclick registration failed. Code: %s", response.get('response_code')))
            except Exception as e:
                _logger.error("Transbank Oneclick: Finish error: %s", str(e))
                self._set_error(str(e))

    def _transbank_oneclick_create_token(self, response):
        """ Helper to create a payment.token from Oneclick response. """
        self.ensure_one()
        token = self.env['payment.token'].create({
            'provider_id': self.provider_id.id,
            'payment_method_id': self.payment_method_id.id,
            'partner_id': self.partner_id.id,
            'provider_ref': response.get('tbk_user'),
            'transbank_tbk_user': response.get('tbk_user'),
            'transbank_username': f"odoo_user_{self.partner_id.id}",
            'transbank_card_type': response.get('card_type'),
            'payment_details': f"**** **** **** {response.get('card_number')[-4:]}",
        })
        self.write({'token_id': token.id, 'tokenize': False})
        _logger.info("Transbank Oneclick: Token created for partner %s", self.partner_id.name)
