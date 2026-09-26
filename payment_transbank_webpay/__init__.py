from odoo.addons.payment import setup_provider

from . import controllers
from . import models


def post_init_hook(env):
    # Activate the Webpay payment method now that it exists on the Transbank provider.
    setup_provider(env, 'transbank')
