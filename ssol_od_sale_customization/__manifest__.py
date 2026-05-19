# -- coding: utf-8 --
{
    "name": "Sale Customization OD",

    'version': '17.0.0.0',

    'summary': """Sale Customization OD""",

    'sequence': 1,

    'description': """Sale Customization OD""",

    'category': 'sale',

    'author': "SelectaSol",

    'maintainer': "Mr.Musadiq Fiyaz",

    'website': 'https://selectasol.com',

    "depends": ['base', 'sale', 'sale_management', 'stock', 'account', 'product', 'report_qweb_pdf_watermark'],

    "data": [
        # 'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/res_users_views.xml',
        'report/report.xml',
        'report/custom_header_footer_report.xml',
        'report/copper_quot_report_template.xml',
        'report/copper_quot_report_template_01.xml',
        'report/nh3_quot_report_template.xml',
        'report/nh3_quot_report_template_01.xml',
        'report/other_quot_report_template.xml',
        'report/other_quot_report_template_01.xml',
        # 'report/bill_quot_report_template.xml',
    ],

    'assets': {
        'web.assets_backend': [
            '/ssol_od_sale_customization/static/src/css/styles.css',
        ],
    },

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
