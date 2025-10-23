/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";

class CustomButton extends Component {
    setup() {
        this.pos = usePos();
    }

    async onClick() {
        const order = this.pos.get_order();

        if (!order || order.is_empty()) {
            this.env.services.notification.add("Aucune commande à imprimer", {
                type: "warning",
            });
            return;
        }

        const payload = {
            table: typeof order.get_table === "function" ? order.get_table()?.name : null,
            cashier: this.pos.get_cashier()?.name || "Inconnu",
            pos_config: this.pos.config.name,
            total: order.get_total_with_tax(),
            lines: order.get_orderlines().map((line) => ({
                product_name: line.product.display_name,
                qty: line.quantity,
                uom: line.product.uom_id[1],
                note: line.get_note?.() || "",
            })),
        };

        try {
            const res = await fetch("http://127.0.0.1:5000/print_order", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-KEY": "odoo1234",
                },
                body: JSON.stringify(payload),
            });

            const result = await res.json();
            if (res.ok) {
                this.env.services.notification.add("Commande imprimée 🖨️", {
                    type: "success",
                });
            } else {
                throw new Error(result.error || "Erreur inconnue");
            }
        } catch (err) {
            console.error("Erreur envoi impression :", err);
            this.env.services.notification.add("Erreur : " + err.message, {
                type: "danger",
            });
        }
    }
}

CustomButton.template = "CustomButton";

ProductScreen.addControlButton({
    component: CustomButton,
    condition: () => true,
});

export default CustomButton;
