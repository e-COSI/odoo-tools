# -*- coding: utf-8 -*-


class Inspect(object):

    def __init__(self, odoo):
        self._odoo = odoo


    def relations(self, models, maxdepth=1, whitelist=None, blacklist=None,
                  attrs_whitelist=None, attrs_blacklist=None, config=None):
        from relations import Relations
        return Relations(
            self._odoo, models, maxdepth, whitelist, blacklist,
            attrs_whitelist, attrs_blacklist, config)

    def dependencies(self, modules=None, models=None, models_blacklist=None,
                     restrict=False, config=None):
        from dependencies import Dependencies
        return Dependencies(
            self._odoo, modules, models, models_blacklist, restrict, config)
