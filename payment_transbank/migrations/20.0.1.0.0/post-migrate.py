import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Restrict upgraded Transbank providers to CLP.

    `available_currency_ids` is a stored compute that only depends on `code`, so an upgrade keeps
    the CLP + USD set computed on 19.0. Since 20.0 amounts are sent as CLP integers: a USD
    payment would charge a wrong amount, so the currencies are recomputed.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    providers = env['payment.provider'].with_context(active_test=False).search([('code', '=', 'transbank')])
    for provider in providers:
        previous_currencies = provider.available_currency_ids
        provider._compute_available_currency_ids()
        removed_currencies = previous_currencies - provider.available_currency_ids
        if removed_currencies:
            _logger.warning(
                'Transbank provider %s (company %s): removed currencies %s, only CLP is supported.',
                provider.id,
                provider.company_id.name,
                ', '.join(removed_currencies.mapped('name')),
            )
