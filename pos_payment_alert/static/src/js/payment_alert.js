/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

console.log("✅ payment_alert.js chargé !");

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        alert("✅ Paiement validé !");
        return await PaymentScreen.prototype.validateOrder.call(this, isForceValidate);
    },
});
