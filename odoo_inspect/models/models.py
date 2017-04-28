# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import logging
import odoorpc, inspect
import base64


_logger = logging.getLogger(__name__)

class OdooInspect(odoorpc.ODOO):

    def __init__(self, host='localhost', protocol='jsonrpc',
                 port=8069, timeout=120, version=None, opener=None):
        super(OdooInspect, self).__init__(host, protocol, port, timeout, version, opener)
        self._inspect = inspect.Inspect(self)

    inspect = property(lambda self: self._inspect, doc="")


class OdooInspectManager(models.Model):
    _name = "odoo.inspect"

    name = fields.Char(required=True)
    host = fields.Char(default="localhost", required=True)
    port = fields.Integer(default=8069, required=True)
    database = fields.Char(required=True)
    username = fields.Char(required=True)
    password = fields.Char(required=True)

    @api.multi
    def _get_graph_name(self):
        for record in self:
            base_name = "unnamed"
            if record.model_list:
                base_name = record.model_list.replace(",", "_").replace(".", "-")
            self.graph_filename = base_name + "." + record.graph_type

    inspect_mode = fields.Selection(selection=[
        ("rel", _("Relations")),
        ("dep", _("Dependencies")),
    ], default="rel", required=True)
    graph_type = fields.Char(default="svg")
    graph_filename = fields.Char(compute="_get_graph_name")
    graph = fields.Binary(attachment=True, readonly=True)

    model_list = fields.Char()
    white_list = fields.Char()
    black_list = fields.Char()

    max_depth = fields.Integer(default=1)
    attrs_white_list = fields.Char()
    attrs_black_list = fields.Char()
    restrict = fields.Boolean(default=False)

    @api.multi
    def inspect(self):
        for record in self:
            odoo = record._get_inspect_instance()
            filepath = "/tmp/" + record.graph_filename
            graph = None

            try:
                if record.inspect_mode == "rel":
                    graph = self._inspect_relations(odoo)
                if record.inspect_mode == "dep":
                    graph = self._inspect_dependencies(odoo)
                if graph:
                    graph.write(filepath, format=record.graph_type)
                    graph_file = open(filepath, 'rb')
                    record.graph = base64.b64encode(graph_file.read())
            except Exception as e:
                _logger.exception(e)
                raise UserError(repr(e))

    def _inspect_relations(self, odoo):
        return odoo.inspect.relations(
            models=self._clean_list(self.model_list),
            maxdepth=self.max_depth,
            whitelist=self._clean_list(self.white_list),
            blacklist=self._clean_list(self.black_list),
            attrs_whitelist=self._clean_list(self.attrs_white_list),
            attrs_blacklist=self._clean_list(self.attrs_black_list),
        )

    def _inspect_dependencies(self, odoo):
        return odoo.inspect.dependencies(
            modules=self._clean_list(self.white_list),
            models=self._clean_list(self.model_list),
            models_blacklist=self._clean_list(self.black_list),
            restrict=self.restrict,
        )

    def _get_inspect_instance(self):
        try:
            inst = OdooInspect(self.host, port=self.port)

            inst.login(self.database, self.username, self.password)
            return inst

        except Exception as e:
            _logger.exception(e)
            raise UserError(repr(e))

    @staticmethod
    def _clean_list(field):
        if field:
            _logger.warning("Field: " + field)
            return [s.strip() for s in field.split(",")]
        return []
