from urllib.parse import urlencode

import requests
from transbank.error.transbank_error import TransbankError
from transbank.webpay.webpay_plus.transaction import Transaction as WebpayPlusTransaction

from odoo import models
from odoo.tools import consteq
from odoo.tools.urls import urljoin

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.payment_transbank import const
from odoo.addons.payment_transbank_webpay.controllers.main import WebpayController

_logger = get_payment_logger(__name__, const.SENSITIVE_KEYS)

# Errors after which the outcome of a Transbank call is unknown (network, non-JSON body).
UNKNOWN_OUTCOME_ERRORS = (requests.exceptions.RequestException, ValueError)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if not self._transbank_is_webpay():
            return res

        query = urlencode({'reference': self.reference})
        return_url = urljoin(self.provider_id.get_base_url(), f'{WebpayController._return_url}?{query}')
        try:
            response = self._transbank_webpay_client().create(
                buy_order=self.reference,
                session_id=self._transbank_session_id(),
                amount=int(self.currency_id.round(self.amount)),
                return_url=return_url,
            )
        except (TransbankError, *UNKNOWN_OUTCOME_ERRORS):
            _logger.warning('Webpay Plus: could not create the transaction %s', self.reference, exc_info=True)
            response = None
        if not isinstance(response, dict):
            self._set_error(self.env._('Could not initiate the Webpay payment. Please try again later.'))
            return {}

        # The token expires 5 minutes after its creation: the customer is redirected right away.
        self.provider_reference = response['token']
        # The redirect form template only receives these values: it needs provider_code too.
        return {'api_url': response['url'], 'token_ws': response['token'], 'provider_code': self.provider_code}

    def _transbank_is_webpay(self):
        return self.provider_code == 'transbank' and self.payment_method_code == 'webpay'

    def _transbank_session_id(self):
        """Return a per-transaction secret sent as Webpay session_id (max 61 chars).

        Webpay sends it back as TBK_ID_SESION when the payment form times out, which proves that the
        return comes from Webpay: the order number alone is not a secret.
        """
        return payment_utils.generate_access_token(self.id, self.reference, env=self.env)[:32]

    def _transbank_webpay_client(self):
        return WebpayPlusTransaction(self.provider_id._get_transbank_options('webpay'))

    def _transbank_get_return_payment_data(self, data):
        """Turn the parameters received on the Webpay return URL into payment data for `_record`.

        Webpay returns four combinations: `token_ws` alone (paid or rejected), `TBK_TOKEN` (aborted),
        `token_ws` with `TBK_TOKEN` (error on the payment form) and neither token (timeout). Data
        that does not match this transaction is ignored, so a forged request cannot change it.

        :param dict data: The parameters of the return URL.
        :return: The payment data, or None if the data must be ignored.
        :rtype: dict | None
        """
        self.ensure_one()
        payment_data = {'reference': self.reference}
        tbk_token = data.get('TBK_TOKEN')
        token_ws = data.get('token_ws')
        if tbk_token:  # Aborted or failed on the Webpay form: the payment must never be committed.
            if not self._transbank_is_same(tbk_token, self.provider_reference):
                return None
            return {**payment_data, 'transbank_flow': 'aborted'}
        if token_ws:
            if not self._transbank_is_same(token_ws, self.provider_reference):
                return None
            return {**payment_data, **self._transbank_commit(token_ws)}
        # The docs spell the session variable both ways.
        session_id = data.get('TBK_ID_SESION') or data.get('TBK_ID_SESSION') or ''
        if data.get('TBK_ORDEN_COMPRA') == self.reference and self._transbank_is_same(
            session_id, self._transbank_session_id()
        ):
            return {**payment_data, 'transbank_flow': 'timeout'}
        return None

    def _transbank_is_same(self, received, expected):
        return bool(expected) and consteq(received.encode(), expected.encode())

    def _transbank_commit(self, token):
        """Confirm the payment at Transbank and return the result as payment data.

        A commit whose outcome is unknown must not fail the transaction: the card may have been
        charged. It stays pending and the next return (or a new commit) reconciles it.
        """
        client = self._transbank_webpay_client()
        try:
            response = client.commit(token)
        except UNKNOWN_OUTCOME_ERRORS:
            _logger.warning('Webpay Plus: unknown commit outcome for %s', self.reference, exc_info=True)
            return {'transbank_flow': 'unknown'}
        except TransbankError as error:
            if error.code != 422:
                _logger.warning('Webpay Plus: commit of %s failed (HTTP %s)', self.reference, error.code)
                return {'transbank_flow': 'failed'}
            # Already committed, e.g. by an earlier attempt whose answer was lost: read the result.
            try:
                response = client.status(token)
            except (TransbankError, *UNKNOWN_OUTCOME_ERRORS):
                _logger.warning('Webpay Plus: no status available for %s', self.reference, exc_info=True)
                return {'transbank_flow': 'unknown'}
        if not isinstance(response, dict):
            return {'transbank_flow': 'unknown'}
        return {**response, 'transbank_flow': 'commit'}

    def _apply_updates(self, payment_data):
        if not self._transbank_is_webpay() or self.operation == 'refund':
            return super()._apply_updates(payment_data)

        flow = payment_data.get('transbank_flow')
        if flow == 'aborted':
            self._set_canceled(state_message=self.env._('The payment was cancelled on Webpay.'))
        elif flow == 'timeout':
            self._set_canceled(state_message=self.env._('The Webpay payment form timed out.'))
        elif flow == 'unknown':
            self._set_pending(state_message=self.env._('Waiting for the confirmation of Transbank.'))
        elif flow == 'failed':
            self._set_error(self.env._('Webpay could not confirm the payment.'))
        elif flow == 'commit':
            self._transbank_apply_commit(payment_data)
        else:
            _logger.warning('Webpay Plus: unexpected payment data for %s', self.reference)
        return None

    def _transbank_apply_commit(self, payment_data):
        card_number = (payment_data.get('card_detail') or {}).get('card_number') or ''
        self.write(
            {
                'transbank_response_code': payment_data.get('response_code'),
                'transbank_status': payment_data.get('status'),
                'transbank_authorization_code': payment_data.get('authorization_code'),
                'transbank_payment_type_code': payment_data.get('payment_type_code'),
                'transbank_card_number': card_number[-4:],  # Never store more than the last 4 digits.
            }
        )
        if payment_data.get('buy_order') != self.reference:
            self._set_error(self.env._('The Webpay order number does not match the transaction.'))
        elif payment_data.get('response_code') == 0 and payment_data.get('status') == 'AUTHORIZED':
            self._set_done()
        else:
            # The meaning of each code depends on the level configured at Transbank: show only the number.
            self._set_error(
                self.env._(
                    'Webpay rejected the payment (code %(code)s). No charge was made.',
                    code=payment_data.get('response_code'),
                )
            )
