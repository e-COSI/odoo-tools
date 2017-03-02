# -*- coding: utf-8 -*-

from odoo import models, fields, api

from subprocess import call
from os import listdir
from os.path import isfile, join, exists
from ast import literal_eval
from shutil import copytree


class GithubSource(models.Model):
    _name = "module_install.github_source"

    token = fields.Char()
    repository_owner = fields.Char()
    repository_name = fields.Char()
    branch = fields.Char(default="master")
    # TO DO: handle specific git tag or repo subdirectory
    tag = fields.Char(default="latest")
    subdir = fields.Char()

    def _clone_github_repository(self):
        # TO DO: raise a waring popup in case credentials are missing or invalid
        repo_url = "github.com/{0}/{1}.git".format(self.repository_owner, self.repository_name)
        folder_id = "{0}_{1}_{2}_{3}" \
            .format(self.repository_owner, self.repository_name, self.branch, self.tag)
        # TO DO: raise a warning if source has already been fetched
        cmd = "git clone https://{0}@{1} -b {2} /tmp/{3}" \
            .format(self.token, repo_url, self.branch, folder_id)
        if call(cmd, shell=True) == 0:
            print "Module installed succesfully"
            return folder_id
        return ""


class Source(models.Model):
    _name = "module_install.source"
    _inherit = ["module_install.github_source",]

    source_type = fields.Selection(selection=[
        ('G', "Github"),
        ('S', "SFTP"),
        ('Z', "Zip"),
    ], string="Source type", default="G")

    @api.multi
    def get_source(self):
        root_path = "/tmp"
        folder_id = ""
        if self.source_type == 'G':
            folder_id = self._clone_github_repository()
        elif self.source_id == 'Z':
            pass
        elif self.source_id == 'S':
            pass
        if folder_id:
            self.check_module("/tmp", folder_id, True)
        return {
            'type': 'ir.actions.act_window',
            'name': "Source modules",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'module_install.wizard',
        }

    def _check_module(self, root_path, folder_id, rec=False):
        path = join(root_path, folder_id)
        if not isfile(path):
            for f in listdir(path):
                filepath = join(path, f)
                if f == "__manifest__.py":
                    datafile = open(filepath, 'r').read()
                    data = literal_eval(datafile)
                    # TO DO: check if corresponding wizard already exists
                    self.env["module_install.wizard"].create({
                        'source': self.id,
                        'module_name': folder_id,
                        'folder_path': path
                        })
                    print "Module {} found".format(data["name"])
                    return True
                if rec:
                    self._check_module(path, f)
        return False


class WizardModule(models.TransientModel):
    _name = "module_install.wizard"

    source = fields.Many2one("module_install.source", required=True)
    module_name = fields.Char(string="module")
    folder_path = fields.Char()

    @api.multi
    def install_module(self):
        if not self.folder_path or not exists(self.folder_path):
            self.source.get_source()
        copytree(self.folder_path, join("/opt/module_install", self.module_name))



