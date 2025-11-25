/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Dialog } from "@web/core/dialog/dialog";

registry.category("actions").add("pos_session_closed_success", async (env, action) => {
    Dialog.confirm(env, action.message || "Session POS fermée !");
});
