/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

const _superSend = PosStore.prototype.sendOrderInPreparation;

patch(PosStore.prototype, {
    async sendOrderInPreparation(order, cancelled = false) {
        // 1) Uniquement les nouvelles lignes (celles qui partent à la cuisine)
        const changes = order?.changesToOrder ? order.changesToOrder(cancelled) : { new: [], cancelled: [] };
        const newItems = Array.isArray(changes.new) ? changes.new : [];

        if (!newItems.length) {
            console.log("ℹ️ [pos_order_alert] Aucune nouvelle ligne -> rien à envoyer.");
            if (_superSend) return _superSend.call(this, order, cancelled);
            return;
        }

        // 2) Commande courante
        const currentOrder =
            this.pos?.get_order?.() ??
            this.get_order?.() ??
            order;

        // 3) Nom de table (robuste)
        const tableName =
            currentOrder?.table?.name ??
            currentOrder?.getTable?.()?.name ??
            currentOrder?.get_table?.()?.name ??
            this.pos?.table?.name ??
            null;

        // 4) Normalise une ligne "new" avec catégorie POS
        const normalize = (it) => {
            const byIdLine = (it?.id && currentOrder?.get_orderline)
                ? currentOrder.get_orderline(it.id)
                : null;

            const product = it.product || byIdLine?.product || null;

            const categoryName =
                it.category_name ??
                product?.pos_categ_id?.[1] ??
                byIdLine?.get_product?.()?.pos_categ_id?.[1] ??
                null;

            return {
                product_name:
                    it.product_name ??
                    product?.display_name ??
                    it.name ??
                    "Produit",
                qty: it.qty ?? it.quantity ?? it.new_qty ?? it.get_quantity?.() ?? 1,
                uom: it.uom_name ?? it.uom?.[1] ?? product?.uom_id?.[1] ?? "Unité(s)",
                category: categoryName,
                note: it.note ?? it.customer_note ?? it.kitchen_note ?? it.get_note?.() ?? "",
            };
        };

        // 5) Construction du payload
        const payload = {
            table: tableName,
            cashier: (this.pos?.get_cashier?.()?.name) || (this.get_cashier?.()?.name) || "Inconnu",
            pos_config: (this.pos?.config?.name) || (this.config?.name) || "POS",
            total: currentOrder.get_total_with_tax(),
            lines: newItems.map(normalize),
        };

        // 6) Envoi vers app.py : /print_order
        try {
            const res = await fetch("http://localhost:5000/print_order", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-KEY": "odoo1234",
                },
                body: JSON.stringify(payload),
            });
            const result = await res.json();
            console.log("🖨️ Envoi réussi à /print_order :", result);
        } catch (error) {
            console.error("❌ Erreur d'envoi à l'imprimante :", error);
        }

        // 7) Continuer comportement natif
        if (_superSend) {
            return _superSend.call(this, order, cancelled);
        }
    },
});

console.log("✅ [order_alert] chargé avec envoi vers /print_order");
