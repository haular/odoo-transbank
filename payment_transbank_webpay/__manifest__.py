{
    'name': 'Transbank Webpay Plus',
    'version': '1.0.0',
    'category': 'Accounting/Payment Providers',
    'author': 'Héctor Aular <aular.hector.dev@gmail.com>',
    'summary': 'Adds Webpay Plus payment method to Transbank provider.',
    'depends': ['payment_transbank'],
    'data': [
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_transbank_templates.xml',
    ],
    'license': 'LGPL-3',
}