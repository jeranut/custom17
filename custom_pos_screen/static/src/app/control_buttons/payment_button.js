/** @odoo-module **/

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

console.log("✅ ProductCombosButton loaded");

export class ProductCombosButton extends Component {
    static template = "custom_pos_screen.ProductCombosButton";

    setup() {
        this.pos = usePos();
        this.action = useService("action");
        this.orm = useService("orm");
    }

    async click() {
        console.log("🟢 ProductCombosButton clicked — opening folio list");

        try {
            // Appel Python -> récupère l'action des folios
            const result = await this.orm.call("pos.folio.filter", "get_folio_action", []);
            // Ouvre la fenêtre native Odoo avec la liste des folios
            await this.action.doAction(result);
        } catch (error) {
            console.error("❌ Error while opening folio list:", error);
        }
    }
}

// ✅ Patch du PaymentScreen
patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        console.log("🔄 PaymentScreen patched with ProductCombosButton");
    },
});

PaymentScreen.components = {
    ...(PaymentScreen.components || {}),
    ProductCombosButton,
};
