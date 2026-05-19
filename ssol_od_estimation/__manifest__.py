# -- coding: utf-8 --
{
    "name": "Estimation OD",

    'version': '17.0.0.0',

    'summary': """Estimation OD""",

    'sequence': 1,

    'description': """Estimation OD""",

    'category': 'sale',

    'author': "SelectaSol",

    'maintainer': "Mr.Musadiq Fiyaz",

    'website': 'https://selectasol.com',

    "depends": ['base', 'sale', 'sale_management', 'stock', 'account', 'product'],

    "data": [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence_data.xml',
        'views/menus.xml',
        'views/order_estimation_views.xml',
        'views/gi_order_views.xml',
        'views/ms_channel_views.xml',
        'views/ms_flat_views.xml',
        'views/ms_angle_views.xml',
        'views/ms_sheet_views.xml',
        'views/ms_plate_views.xml',
        'views/ms_square_views.xml',
        'views/ms_round_views.xml',
        'views/ms_pipe_views.xml',
        'views/ms_tube_copy_views.xml',
        # 'views/ms_tube_views.xml',

        'views/ss_flats_views.xml',
        'views/ss_angles_views.xml',
        'views/ss_rods_views.xml',
        'views/ss_sheets_views.xml',
        'views/ss_pipe_views.xml',

        'views/copper_tube_views.xml',
        'views/copper_sheet_views.xml',

        'views/aluminum_sheet_views.xml',
        'views/finished_goods_views.xml',

        'views/mrp_production_order_views.xml',
    ],

    'assets': {
            'web.assets_backend': [
                '/ssol_od_estimation/static/src/css/styles.css',
        ],
    },

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
