from odoo.modules.module import load_script
from odoo.tests import tagged
from odoo.tools import file_path, mute_logger

from odoo.addons.payment.tests.common import PaymentCommon


@tagged('post_install', '-at_install')
class TestMigration(PaymentCommon):
    @mute_logger('odoo.upgrade.payment_transbank.20.0.1.0.0.post-migrate')
    def test_upgrade_from_19_restricts_currencies_to_clp(self):
        provider = self._prepare_provider('transbank')
        clp = self._enable_currency('CLP')
        provider.available_currency_ids = clp + self.currency_usd  # As computed on 19.0.
        script = load_script(
            file_path('payment_transbank/migrations/20.0.1.0.0/post-migrate.py'),
            'odoo.upgrade.payment_transbank.20.0.1.0.0.post-migrate',
        )
        script.migrate(self.env.cr, '19.0.1.0.2')
        self.assertEqual(provider.available_currency_ids, clp)
