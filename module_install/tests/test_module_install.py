# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, SingleTransactionCase
import logging, os
from shutil import rmtree


_logger = logging.getLogger(__name__)

class TestModuleInstall(TransactionCase):

    install_folder = "/tmp/test_install_folder"
    module_name = "customizable_backend_theme"

    def test_github_source(self):
        source_model = self.env['module_install.source']
        github_source = source_model.create({
            "name": "Test Source",
            "type": "G",
            "install_folder": self.install_folder,
            "search_depth": 1,
            "token": os.environ["GITHUB_TOKEN"],
            "repository_owner": "e-COSI",
            "repository_name": "odoo-saas-addons",
            "branch": "10.0"
        })[0]
        github_source.get_source()

        self.assertEqual(len(github_source.module_ids), 7,
                         "Current number of modules available in saas addons repository")
        module = self.env['module_install.wizard'].search([
            ('name', '=', self.module_name),
        ])
        self.assertEqual(len(module), 1, "Only one module named: " + self.module_name)
        manifest_path = os.path.join(module[0].folder_path, "__manifest__.py")
        self.assertTrue(os.path.isfile(manifest_path),
                        "Check local module is presend and has a manifest file.")
        #rmtree(self.install_folder)
        _logger.warning("All tests have been done.")


    def test_invalid_source(self):
        source_model = self.env['module_install.source']
        source1 = source_model.create({
            "name": "Test 2",
            "type": "G",
            "install_folder": "/no-right-zone",
            "token": os.environ["GITHUB_TOKEN"],
            "repository_owner": "e-COSI",
            "repository_name": "trash-repo",
        })[0]
        source1.get_source()
        _logger.warning("Invalid source logs: " + source1.logs)
