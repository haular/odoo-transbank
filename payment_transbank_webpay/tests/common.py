from odoo.addons.payment.tests.common import PaymentCommon

TOKEN = 'e9d555262db0f989e49d724b4db0b0af367cc415cde41f500a776550fc5fddd3'


class WebpayCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.transbank = cls._prepare_provider('transbank')
        cls.provider = cls.transbank
        cls.currency = cls._enable_currency('CLP')
        cls.payment_method = cls.env.ref('payment_transbank_webpay.payment_method_webpay')
        cls.payment_method_id = cls.payment_method.id
        cls.payment_method_code = cls.payment_method.code
        cls.amount = 15990
        cls.reference = 'TB-TEST-1'
        cls.commit_response = {
            'vci': 'TSY',
            'amount': 15990,
            'status': 'AUTHORIZED',
            'buy_order': cls.reference,
            'session_id': cls.reference,
            'card_detail': {'card_number': '6623'},
            'accounting_date': '0926',
            'transaction_date': '2026-09-26T16:41:21.063Z',
            'authorization_code': '1213',
            'payment_type_code': 'VN',
            'response_code': 0,
            'installments_number': 0,
        }
