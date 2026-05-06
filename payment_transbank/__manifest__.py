{
    'name': 'Payment Provider: Transbank',
    'version': '19.0.1.0.2',
    'category': 'Accounting/Payment Providers',
    'author': 'Héctor Aular',
    'sequence': 350,
    'summary': 'A Chilean payment provider covering Webpay Plus.',
    'depends': ['payment'],
    'external_dependencies': {
        'python': ['transbank-sdk'],
    },
    'data': [
        'views/payment_transbank_templates.xml',
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_transaction_views.xml',
    ],
    'images': ['static/description/cover.png'],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
