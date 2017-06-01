# -*- coding: utf-8 -*-
{
    'name': "e-COSI Module Install",

    'summary': """
        Install tool use to fetch modules available via Github or SFTP and can also upload zipped module sources.
     """,

    'description': """
        Install tool use to fetch modules available via Github or SFTP and can also upload zipped module sources.
    """,

    'author': "odoo@e-cosi.com",
    'website': "http://www.e-cosi.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '1.2.0',

    # any module necessary for this one to work correctly
    'depends': ['web_x2many_selectable',],

    # always loaded
    'data': [
        'views/views.xml',

        'data/source_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

}