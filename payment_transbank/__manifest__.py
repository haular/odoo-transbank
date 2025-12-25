{
    'name': 'Payment Provider: Transbank',
    'version': '1.0.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': 'A Chilean payment provider covering Webpay Plus and Oneclick.',
    'depends': ['payment', 'portal'],
    'external_dependencies': {
        'python': ['transbank'],
    },
    'data': [
        'data/payment_method_data.xml',
        'views/payment_transbank_templates.xml',
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
