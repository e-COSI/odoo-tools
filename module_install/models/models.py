# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Source(models.Model):
    _name = "module_install.source"

    source_type = fields.Selection([
        ('G', "Github"),
        ('S', "SFTP"),
        ('Z', "Zip"),
    ])
    token = fields.Char()
    repository = fields.Char()
    branch = fields.Char(default="master")
    tag = fields.Char(default="latest")
    subdir = fields.Char()

"""
class Source(models.Model):
    _name = "module_install.source"
    _inherit = ["module_install.github_source",]
"""
