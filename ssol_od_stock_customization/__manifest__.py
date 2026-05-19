# -- coding: utf-8 --
{
    "name": "Stock Customization OD",

    'version': '17.0.0.0',

    'summary': """Stock Customization OD""",

    'sequence': 1,

    'description': """Sale Customization OD""",

    'category': 'stock',

    'author': "SelectaSol",

    'maintainer': "Mr.Musadiq Fiyaz",

    'website': 'https://selectasol.com',

    "depends": ['base', 'stock', 'product'],

    "data": [
        'security/ir.model.access.csv',
        'views/material_type_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'data/sequence.xml',
        'views/product_report_stock_view.xml',
        'views/stock_picking_views.xml',
        'report/report.xml',
        'report/custom_header_footer_report.xml',
        'report/delivery_chalan_report_template.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
