/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

const _superSend = PosStore.prototype.sendOrderInPreparation;

patch(PosStore.prototype, {
    async sendOrderInPreparation(order, cancelled = false) {
        const currentOrder = this.get_order?.() ?? order;

        // 🔎 récupérer uniquement les nouvelles lignes
        const changes = order?.changesToOrder
            ? order.changesToOrder(cancelled)
            : { new: [], cancelled: [] };
        const newItems = Array.isArray(changes.new) ? changes.new : [];

        if (!newItems.length) {
            console.log("⚠️ Aucun nouveau produit sélectionné.");
            if (_superSend) return _superSend.call(this, order, cancelled);
            return;
        }

        const barProducts = [];
        const kitchenProducts = [];

        for (const it of newItems) {
            let product = null;
            if (it.product_id) {
                product = this.db.get_product_by_id(it.product_id);
            }
            if (!product && it.get_product) {
                product = it.get_product();
            }
            if (!product) continue;

            const productName = product.display_name;
            const categoryNames = (product.pos_categ_ids || [])
                .map((catId) => this.db.get_category_by_id(catId)?.name)
                .filter(Boolean);

            // ✅ Catégorie BAR si "boisson" OU "sigare"
            const isBarItem = categoryNames.some(
                (cat) =>
                    cat &&
                    ["boisson", "sigare"].includes(cat.toLowerCase())
            );

            const lineData = {
                product_name: productName,
                qty: it.qty ?? it.quantity ?? 1,
                uom: product.uom_id?.[1] || "u",
                category: categoryNames.join(", "),
                note: it.note || "",
            };

            if (isBarItem) {
                barProducts.push(lineData);
            } else {
                kitchenProducts.push(lineData);
            }
        }

        // 🔹 Récupération table & caissier
        const tableName =
            currentOrder?.table?.name ??
            currentOrder?.getTable?.()?.name ??
            currentOrder?.get_table?.()?.name ??
            null;

        const cashierName =
            (this.pos?.get_cashier?.()?.name) ||
            (this.get_cashier?.()?.name) ||
            "Inconnu";

        // 🔹 Fonction générique pour envoyer un payload
        const sendTo = async (url, payload, label) => {
            try {
                const res = await fetch(url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-API-KEY": "odoo1234",
                    },
                    body: JSON.stringify(payload),
                });
                const result = await res.json();
                console.log(`🖨️ Envoi réussi à ${label}:`, result);
            } catch (error) {
                console.error(`❌ Erreur d'envoi à ${label}:`, error);
            }
        };

        // 🔸 Bar (Boissons + Sigares)
        if (barProducts.length) {
            await sendTo("http://192.168.0.100:5000/print_bar", {
                table: tableName,
                cashier: cashierName,
                pos_config: (this.pos?.config?.name) || "POS",
                total: currentOrder.get_total_with_tax(),
                lines: barProducts,
            }, "/print_bar");
        }

        // 🔸 Cuisine (autres catégories)
        if (kitchenProducts.length) {
            await sendTo("http://192.168.0.100:5000/print_kitchen", {
                table: tableName,
                cashier: cashierName,
                pos_config: (this.pos?.config?.name) || "POS",
                total: currentOrder.get_total_with_tax(),
                lines: kitchenProducts,
            }, "/print_kitchen");
        }

        if (_superSend) {
            return _superSend.call(this, order, cancelled);
        }
    },
});

console.log("✅ [order_alert] chargé (Bar = Boisson + Sigare / Cuisine = autres, sans alertes)");
