# -- coding: utf-8 --
{
    "name": "Mrp Customization OD",

    'version': '17.0.0.0',

    'summary': """Mrp Module Customizations OD""",

    'sequence': 1,

    'description': """Mrp Module Customizations OD""",

    'category': 'mrp',

    'author': "SelectaSol",

    'maintainer': "Mr.Musadiq Fiyaz",

    'website': 'https://selectasol.com',

    "depends": ['base', 'mrp', 'mrp_account', 'product'],

    "data": [
        # 'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
        'reports/report.xml',
        'reports/mrp_ms_coile_report.xml',
        'reports/mrp_ms_cooler_heat_report.xml',
    ],

    'assets': {
        'web.assets_backend': [
            '/ssol_od_mrp_customization/static/src/css/styles.css',
        ],
    },

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
