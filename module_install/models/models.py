# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import logging
from subprocess import call
import os
from os.path import isfile, join, exists
from ast import literal_eval
from shutil import copytree, rmtree
from base64 import b64decode
import zipfile, tarfile


_logger = logging.getLogger(__name__)

def clear_folder(folder_path):
    if exists(folder_path):
        if isfile(folder_path):
            os.remove(folder_path)
        else:
            rmtree(folder_path)

class GithubSource(models.Model):
    _name = "module_install.github_source"

    token = fields.Char(default="")
    repository_owner = fields.Char()
    repository_name = fields.Char()
    branch = fields.Char(default="master")
    # TO DO: handle specific git tag or repo subdirectory
    tag = fields.Char(default="latest")
    subdir = fields.Char()

    def _clone_repository(self):
        # TO DO: raise a warning popup in case credentials are missing or invalid
        repo_url = "github.com/{0}/{1}.git".format(self.repository_owner, self.repository_name)
        folder_id = "{0}_{1}_{2}_{3}" \
            .format(self.repository_owner, self.repository_name, self.branch, self.tag)
        temp_folder = "/tmp/" + folder_id
        # If destination folder already exists delete it and clone again repository
        clear_folder(temp_folder)
        cmd = "git clone https://{0}@{1} -b {2} {3}" \
            .format(self.token, repo_url, self.branch, temp_folder)
        if call(cmd, shell=True) == 0:
            _logger.info(self.repository_name + _(" has been successfully cloned"))
            return folder_id
        return ""


class ZipSource(models.Model):
    _name = "module_install.zip_source"

    zip_file = fields.Binary()
    zip_filename = fields.Char()

    def _unzip_file(self):
        # TO DO: raise a warning if file is not set or invalid
        if self.zip_file:
            temp_zip = "/tmp/" + self.zip_filename
            clear_folder(temp_zip)
            with open(temp_zip, 'wb') as f:
                f.write(b64decode(self.zip_file))
            temp_folder = temp_zip.replace('.', '_')
            clear_folder(temp_folder)
            if zipfile.is_zipfile(temp_zip):
                _logger.info(_("Archive is a zip file."))
                zip_ref = zipfile.ZipFile(temp_zip, 'r')
                zip_ref.extractall(temp_folder)
            elif tarfile.is_tarfile(temp_zip):
                _logger.warning(_("Archive is a tar file."))
                tar_ref = tarfile.open(temp_zip)
                tar_ref.extractall(temp_folder)
            else:
                _logger.warning(_("Unrecognized compression file format."))
            return temp_folder
        return ""

"""
class SFTPSource(models.Model):
    _name = "module_install.sftp_source"

    username = fields.Char()
    password = fields.Char()
    url = fields.Char()
    path = fields.Char()

    def _get_directory(self):
        # TO DO: handle SFTP connexion and fetch modules
        return ""
"""

class Source(models.Model):
    _name = "module_install.source"
    _inherit = ["module_install.github_source", "module_install.zip_source"]

    source_name = fields.Char(required=True)
    source_type = fields.Selection(selection=[
        ('G', "Github"),
        #('S', "SFTP"),
        ('Z', "Zip"),
    ], string="Source type", default="G", required=True)
    source_install_folder = fields.Char(required=True)
    search_depth = fields.Integer(default=0)
    module_ids = fields.One2many('module_install.wizard', 'source', string="Source modules")

    @api.constrains('search_depth')
    def _check_depth(self):
        _MAX_DEPTH = 5
        for record in self:
            if record.search_depth < 0:
                raise ValidationError(_("Search depth must be a positive value."))
            elif record.search_depth > _MAX_DEPTH:
                msg = _("Maximum search depth allowed is {}.").format(_MAX_DEPTH)
                raise ValidationError(msg)

    @api.multi
    def get_source(self):
        for record in self:
            folder_id = ""
            record._check_fields()
            if record.source_type == 'G':
                folder_id = record._clone_repository()
            elif record.source_type == 'Z':
                folder_id = record._unzip_file()
            #elif self.source_type == 'S':
            #    folder_id = self._get_directory()
            if folder_id:
                record._find_module(join("/tmp", folder_id), self.search_depth)
            else:
                msg = _("No modules found with search level {}".format(record.search_depth))
                raise UserWarning(msg)

    def _check_fields(self):
        if self.source_type == 'G':
            github_fields = ['repository_owner', 'repository_name', 'branch']
            missing_fields = [f for f in github_fields if not getattr(self, f)]
            if len(missing_fields) > 0:
                msg = _("Missing github fields ({}) to clone modules.") \
                    .format(", ".join(missing_fields))
                raise UserError(msg)
        elif self.source_type == 'Z':
            if not self.zip_file:
                raise UserError(_("Zip file not set to extract modules."))

    def _find_module(self, path, depth=0):
        #path = join(root_path, folder_id)
        if not isfile(path):
            module_model = self.env["module_install.wizard"]
            """
            old_modules = module_model.search(['source.id', '=', self.id])
            for m in old_modules:
                msg = "Clearing module {0} for source {1}".format(m, self.source_name)
                _logger.warning(msg)
                m.unlink()
            """
            for filename in os.listdir(path):
                _logger.warning("Searching modules in {0} - depth: {1}".format(path, depth))
                filepath = join(path, filename)
                if depth > 0:
                    if not isfile(filepath):
                        self._find_module(filepath, depth - 1)
                elif filename == "__manifest__.py":
                    datafile = open(filepath, 'r').read()
                    data = literal_eval(datafile)
                    values = {
                        'source': self.id,
                        'name': data['name'],
                        'version': data['version'],
                        'folder_path': path
                    }
                    records = module_model.search([
                        ('folder_path', '=', path),
                    ])
                    _logger.warning(str(len(records)) + _(" modules found"))
                    if len(records) == 0:
                        module_model.create(values)
                    else:
                        records.ensure_one()
                        records.write(values)
                    #_logger.info("Module {} found".format(data["name"]))

    @api.multi
    def write(self, vals):
        _logger.warning(vals)
        if 'source_type' in vals and vals['source_type'] != self.source_type:
            raise UserError(_("Cannot change source type after source creation"))
        else:
            return super(Source, self).write(vals)


class WizardModule(models.TransientModel):
    _name = "module_install.wizard"

    source = fields.Many2one("module_install.source", required=True, ondelete='cascade')
    name = fields.Char()
    version = fields.Char()
    folder_path = fields.Char()

    @api.multi
    def install_module(self):
        # Checks if module tmp folder exists, regenerate its source otherwise
        for record in self:
            if not record.folder_path or not exists(record.folder_path) \
                or isfile(record.folder_path) \
                or not isfile(record.folder_path + "/__manifest__.py"):
                record.source.get_source()
                msg = _("A problem occurred while downloading module {}, reloading source files") \
                    .format(record.name)
                raise UserError(msg)
            dest = join(record.source.source_install_folder, record.name)
            try:
                clear_folder(dest)
                copytree(record.folder_path, dest)
                msg = _("Module {0} succesfulled copied to {1}").format(record.name, dest)
                raise UserWarning(msg)
            except Exception as e:
                raise UserError(repr(e))
