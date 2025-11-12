/** @odoo-module **/

console.log("✅ POS Custom Button JS loaded successfully");

import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        console.log("🔄 PaymentScreen patch applied");
    },

    async onClickCustomButton() {
        console.log("🟢 Custom Button clicked");

        await this.showPopup("ConfirmPopup", {
            title: _t("Custom Alert"),
            body: _t("You clicked the custom button"),
            confirmText: _t("OK"),
        });
    },
});
