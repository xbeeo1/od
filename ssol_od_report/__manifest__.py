# -- coding: utf-8 --
{
    "name": "Reporting Customization OD",

    'version': '17.0.0.0',

    'summary': """Reporting Customization OD""",

    'sequence': 1,

    'description': """Reporting Customization OD""",

    'author': "SelectaSol",

    'maintainer': "Mr.Musadiq Fiyaz",

    'website': 'https://selectasol.com',

    "depends": ['base', 'account', 'ssol_od_account_customization'],

    "data": [
        'security/ir.model.access.csv',
        'views/account_payment_tree_views.xml',
        'views/wht_report_wizard_views.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
