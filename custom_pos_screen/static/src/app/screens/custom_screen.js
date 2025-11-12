/** @odoo-module **/

import { PosScreen } from "@point_of_sale/app/screens/pos_screen/pos_screen"; // ✅ plus d'AbstractScreen
import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/store/pos_hook";

console.log("✅ CustomScreen JS loaded!");

export class CustomScreen extends PosScreen {
    setup() {
        super.setup();
        this.pos = usePos();
        console.log("🟢 CustomScreen setup completed");
    }

    back() {
        this.pos.showScreen("ProductScreen"); // ✅ méthode correcte OWL2
    }
}

// ✅ Nom du template QWeb
CustomScreen.template = "custom_pos_screen.CustomScreen";

// ✅ Enregistrement de l'écran dans le registre POS
registry.category("pos_screens").add("CustomScreen", CustomScreen);

console.log("✅ CustomScreen registered in pos_screens");
