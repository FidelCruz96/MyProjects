# -*- coding: utf-8 -*-
{
    'name': "Plan de Ventas",

    'summary': """
        Servicio de Streaming
        """,

    'description': """
    """,

    'author': "GRUPO QUANAM S.A.C.",
    'website': "https://www.grupoquanam.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Personalization',
    'version': '16.0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale',
                
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        #'data/data.xml',
    ],

    'license': 'LGPL-3',
}