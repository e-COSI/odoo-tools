# -*- coding: utf-8 -*-
{
    'name': "e-COSI OdooRPC Inspection Tool",

    'summary': """
        OERPLib inspect tool adapter for OdooRPC to work with Odoo 10.
    """,
    'description': """
       This module is a wrapper to search for relations and dependencies of modules and models
       within Odoo. It is a adapter of the OERPLib inspection tools to integrate it within the
       newer OdooRPC library and use its features with Odoo 10.
       OdooRPC must be installed on the server before using this module.
    """,

    'author': "odoo@e-cosi.com",
    'website': "http://www.e-cosi.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tool',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}