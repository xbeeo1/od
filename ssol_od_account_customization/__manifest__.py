# -- coding: utf-8 --
{
    "name": "Invoicing Customization OD",

    'version': '17.0.0.0',

    'summary': """Invoicing Customization OD""",

    'sequence': 1,

    'description': """Invoicing Customization OD""",

    'category': 'account',

    'author': "SelectaSol",

    'maintainer': "Mr.Musadiq Fiyaz",

    'website': 'https://selectasol.com',

    "depends": ['base', 'sale', 'sale_management', 'stock', 'account', 'product', 'ssol_od_sale_customization'],

    "data": [
        # 'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'wizard/account_payemnt_register_wizard_view.xml',
        'views/account_payment_views.xml',
        'report/report.xml',
        'report/copper_invoice_report_template.xml',
        'report/copper_invoice_report_template_01.xml',
        'report/bill_quot_report_template.xml',
        'report/custom_header_footer_report.xml',
    ],


    'assets': {
            'web.assets_backend': [
                '/ssol_od_account_customization/static/src/css/styles.css',
            ],
        },

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
