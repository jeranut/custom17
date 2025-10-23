/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

const _superSend = PosStore.prototype.sendOrderInPreparation;

patch(PosStore.prototype, {
    async sendOrderInPreparation(order, cancelled = false) {
        const currentOrder = this.get_order?.() ?? order;
        const lines = currentOrder?.get_orderlines?.() || [];

        if (lines.length === 0) {
            alert("⚠️ Aucun produit sélectionné.");
            if (_superSend) return _superSend.call(this, order, cancelled);
            return;
        }

        // Fabrique les messages par ligne (toutes les lignes de la commande)
        const messages = [];
        for (const line of lines) {
            const product = line.get_product?.();
            if (!product) continue;

            const productName = product.display_name;
            const categoryNames = (product.pos_categ_ids || [])
                .map(id => this.db.get_category_by_id(id)?.name)
                .filter(Boolean);

            const isBoisson = categoryNames.some(
                (cat) => cat && cat.toLowerCase() === "boisson"
            );

            if (isBoisson) {
                messages.push(`🥤 Produit BOISSON : ${productName}`);
            } else {
                messages.push(`🚫 Ce n'est pas une boisson`);
            }
        }

        // Affiche les alertes SEQUENTIELLEMENT pour éviter que seule la dernière apparaisse
        messages.forEach((msg, idx) => {
            setTimeout(() => alert(msg), idx * 200);
        });

        if (_superSend) {
            return _superSend.call(this, order, cancelled);
        }
    },
});

console.log("✅ [pos_order_alert] module chargé (alertes séquentielles + filtre strict Boisson)");
