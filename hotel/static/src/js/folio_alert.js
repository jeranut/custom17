/** @odoo-module **/

import { registry } from "@web/core/registry";

function showFolioStateAlert(action, options) {
    alert("L'état actuel du folio est : " + action.params.state);
    return Promise.resolve();
}

registry.category("actions").add("display_folio_state_alert", showFolioStateAlert);
