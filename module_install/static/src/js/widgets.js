odoo.define('web_x2many_selectable.form_widgets', function (require) {
    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var _t = core._t;
    var QWeb = core.qweb;
    var FieldOne2Many = core.form_widget_registry.get('one2many');

    var X2ManySelectable = FieldOne2Many.extend({
        multi_selection: true,
        init: function () {
            this._super.apply(this, arguments);
        },
        start: function () {
            this._super.apply(this, arguments);
            var self = this;
            this.$el.after(QWeb.render("X2ManySelectable", {widget: this}));
            this.$el.next().find(".ep_button_confirm").click(function () {
                self.action_selected_lines('install_module', self.handle_install);
            });
            this.$el.next().find(".ep_button_check").click(function () {
                self.action_selected_lines('check_module', self.check_install);
            });
        },

        action_selected_lines: function (py_method_id, js_handler) {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            var model_obj = new Model(self.dataset.model);
            model_obj.call(py_method_id, [selected_ids], {context: self.dataset.context})
                .then(js_handler.bind(self));

        },
        get_selected_ids_one2many: function () {
            var ids = [];

            this.$el.find('tr:has(td.o_list_record_selector:has(input:checked))')
                .each(function () {
                    ids.push(parseInt($(this).context.dataset.id));
                });
            return ids;
        },

        handle_install: function(data) {
            if (data[0] == 0) {
                this.do_notify(data[1].join("\n"));
            } else {
                this.do_warn(_t("Error"), data[1]);
            }

        },
        check_install: function(data) {
            for (var i = 0; i < data.length; i++) {
                var elm = data[i];

                if (elm[0] == 0) {
                    this.do_warn(_t("Error"), elm[1] + _t(" is not available yet"))
                } else {
                    this.do_notify(
                        _t("Current version: [") + elm[0].toString() + "]",
                        elm[1] + _t(" available")
                    )
                }
            }
        },
    });
    core.form_widget_registry.add('x2many_selectable', X2ManySelectable);
    return X2ManySelectable;
});
