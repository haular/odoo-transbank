from unittest.mock import patch

import requests
from transbank.error.transaction_commit_error import TransactionCommitError
from transbank.webpay.webpay_plus.transaction import Transaction as WebpayPlusTransaction

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon
from odoo.addons.payment_transbank_webpay.controllers.main import WebpayController
from odoo.addons.payment_transbank_webpay.tests.common import TOKEN, WebpayCommon

LOGGERS = (
    'odoo.addons.payment_transbank_webpay.controllers.main',
    'odoo.addons.payment_transbank_webpay.models.payment_transaction',
)


@tagged('post_install', '-at_install')
class TestWebpay(WebpayCommon, PaymentHttpCommon):
    def setUp(self):
        super().setUp()
        self._disable_process_patcher()

    def _return_from_webpay(self, params, commit=None, status=None):
        """Simulate the customer's return from Webpay and run the payment processing."""
        commit = commit or {'return_value': self.commit_response}
        url = self._build_url(WebpayController._return_url)
        with (
            patch.object(WebpayPlusTransaction, 'commit', **commit) as commit_mock,
            patch.object(WebpayPlusTransaction, 'status', **(status or {})) as status_mock,
        ):
            self._make_http_get_request(url, params={'reference': self.reference, **params})
        self._run_processing()
        return commit_mock, status_mock

    def test_long_reference_is_shortened_for_buy_order(self):
        reference = self.env['payment.transaction']._compute_reference('transbank', prefix='INV/2026/00001-INV/2026/00002')
        self.assertLessEqual(len(reference), 26)
        self.assertTrue(self.env['payment.transaction']._transbank_is_valid_buy_order(reference))

    def test_valid_reference_is_kept(self):
        reference = self.env['payment.transaction']._compute_reference('transbank', prefix='S00042')
        self.assertEqual(reference, 'S00042')

    def test_rendering_values_create_the_webpay_transaction(self):
        tx = self._create_transaction('redirect')
        response = {'token': TOKEN, 'url': 'https://webpay3gint.transbank.cl/webpayserver/initTransaction'}
        with patch.object(WebpayPlusTransaction, 'create', return_value=response) as create_mock:
            processing_values = tx._get_processing_values()  # Renders the redirect form, as in checkout.
        form = processing_values['redirect_form_html']
        self.assertIn(response['url'], form)
        self.assertIn('id="o_payment_redirect_form_transbank"', form)
        self.assertIn(f'name="token_ws" value="{TOKEN}"', form)
        self.assertEqual(tx.provider_reference, TOKEN)
        kwargs = create_mock.call_args.kwargs
        self.assertEqual(kwargs['buy_order'], self.reference)
        self.assertEqual(kwargs['amount'], 15990)
        self.assertIsInstance(kwargs['amount'], int)
        self.assertIn('reference=TB-TEST-1', kwargs['return_url'])
        self.assertEqual(kwargs['session_id'], tx._transbank_session_id())
        self.assertNotEqual(kwargs['session_id'], self.reference)
        self.assertLessEqual(len(kwargs['session_id']), 61)

    @mute_logger(*LOGGERS)
    def test_create_failure_sets_a_generic_error(self):
        tx = self._create_transaction('redirect')
        with patch.object(WebpayPlusTransaction, 'create', side_effect=requests.exceptions.ConnectTimeout('secret')):
            tx._get_processing_values()
        self.assertEqual(tx.state, 'error')
        self.assertNotIn('secret', tx.state_message)

    @mute_logger(*LOGGERS)
    def test_approved_payment_is_done(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        self._return_from_webpay({'token_ws': TOKEN})
        self.assertEqual(tx.state, 'done')
        self.assertEqual(tx.transbank_authorization_code, '1213')
        self.assertEqual(tx.transbank_card_number, '6623')

    @mute_logger(*LOGGERS)
    def test_full_card_number_is_not_stored(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        response = dict(self.commit_response, card_detail={'card_number': '4051885600446623'})
        self._return_from_webpay({'token_ws': TOKEN}, commit={'return_value': response})
        self.assertEqual(tx.transbank_card_number, '6623')

    @mute_logger(*LOGGERS)
    def test_null_card_detail_does_not_break_an_approved_payment(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        response = dict(self.commit_response, card_detail=None)
        self._return_from_webpay({'token_ws': TOKEN}, commit={'return_value': response})
        self.assertEqual(tx.state, 'done')

    @mute_logger(*LOGGERS)
    def test_rejected_payment_shows_only_the_code(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        response = dict(self.commit_response, response_code=-1, status='FAILED')
        self._return_from_webpay({'token_ws': TOKEN}, commit={'return_value': response})
        self.assertEqual(tx.state, 'error')
        self.assertIn('-1', tx.state_message)
        self.assertEqual(tx.transbank_response_code, -1)

    @mute_logger(*LOGGERS, 'odoo.addons.payment.models.payment_transaction')
    def test_amount_mismatch_is_an_error(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        response = dict(self.commit_response, amount=100)
        self._return_from_webpay({'token_ws': TOKEN}, commit={'return_value': response})
        self.assertEqual(tx.state, 'error')

    @mute_logger(*LOGGERS)
    def test_buy_order_mismatch_is_an_error(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        response = dict(self.commit_response, buy_order='OTHER-1')
        self._return_from_webpay({'token_ws': TOKEN}, commit={'return_value': response})
        self.assertEqual(tx.state, 'error')

    @mute_logger(*LOGGERS)
    def test_aborted_payment_is_cancelled_without_commit(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        commit_mock, _status_mock = self._return_from_webpay(
            {'TBK_TOKEN': TOKEN, 'TBK_ORDEN_COMPRA': self.reference, 'TBK_ID_SESION': tx._transbank_session_id()}
        )
        self.assertEqual(tx.state, 'cancel')
        commit_mock.assert_not_called()

    @mute_logger(*LOGGERS)
    def test_payment_form_error_is_cancelled_without_commit(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        commit_mock, _status_mock = self._return_from_webpay({'token_ws': TOKEN, 'TBK_TOKEN': TOKEN})
        self.assertEqual(tx.state, 'cancel')
        commit_mock.assert_not_called()

    @mute_logger(*LOGGERS)
    def test_timeout_is_cancelled(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        self._return_from_webpay({'TBK_ORDEN_COMPRA': self.reference, 'TBK_ID_SESION': tx._transbank_session_id()})
        self.assertEqual(tx.state, 'cancel')

    @mute_logger(*LOGGERS)
    def test_forged_tokens_do_not_change_the_transaction(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        commit_mock, _status_mock = self._return_from_webpay({'TBK_TOKEN': 'forged'})
        self._return_from_webpay({'token_ws': 'forged'})
        self._return_from_webpay({'TBK_ORDEN_COMPRA': 'OTHER-1'})
        # The order number is public: without the session secret a "timeout" is ignored.
        self._return_from_webpay({'TBK_ORDEN_COMPRA': self.reference, 'TBK_ID_SESION': self.reference})
        self.assertEqual(tx.state, 'draft')
        commit_mock.assert_not_called()

    @mute_logger(*LOGGERS)
    def test_unknown_commit_outcome_leaves_the_payment_pending(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        self._return_from_webpay({'token_ws': TOKEN}, commit={'side_effect': requests.exceptions.ConnectionError})
        self.assertEqual(tx.state, 'pending')

    @mute_logger(*LOGGERS)
    def test_already_committed_payment_is_read_from_status(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        _commit_mock, status_mock = self._return_from_webpay(
            {'token_ws': TOKEN},
            commit={'side_effect': TransactionCommitError('Transaction already locked by another process', 422)},
            status={'return_value': self.commit_response},
        )
        status_mock.assert_called_once_with(TOKEN)
        self.assertEqual(tx.state, 'done')

    @mute_logger(*LOGGERS)
    def test_commit_rejected_by_transbank_is_an_error(self):
        tx = self._create_transaction('redirect', provider_reference=TOKEN)
        self._return_from_webpay({'token_ws': TOKEN}, commit={'side_effect': TransactionCommitError('Invalid', 401)})
        self.assertEqual(tx.state, 'error')
