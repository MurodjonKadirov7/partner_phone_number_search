/** @odoo-module **/
// Odoo 18: taklifda telefon raqami, tanlangach maydonda faqat ism.
// 18 da web_name_search yo'q; autocomplete yorliq va tanlangan qiymatni bitta
// name_search juftligidan oladi (web/static/src/views/fields/relational_utils.js:314-326).
import { patch } from "@web/core/utils/patch";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";

patch(Many2XAutocomplete.prototype, {
    search(name) {
        if (this.props.resModel !== "res.partner") {
            return super.search(name);
        }
        return this.orm.call("res.partner", "phone_name_search", [], {
            name: name,
            operator: "ilike",
            args: this.props.getDomain(),
            limit: this.props.searchLimit + 1,
            context: this.props.context,
        });
    },
    mapRecordToOption(result) {
        const option = super.mapRecordToOption(result);
        // [id, display_name, label]: label faqat ro'yxatda, display_name tanlanganda
        if (result.length > 2 && result[2]) {
            option.label = result[2];
        }
        return option;
    },
});
