from odoo import models
import requests


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_print_xprinter(self):
        for production in self:
            # Préparer les lignes de consommation
            lines = []
            for move in production.move_raw_ids:
                product = move.product_id.sudo()  # <-- utilise sudo() pour éviter KeyError company_ids
                lines.append({
                    'product_name': product.display_name,
                    'qty': move.product_uom_qty,
                    'uom': move.product_uom.name,
                })

            # Sélection du bon champ de date (Odoo 17)
            date_prod = ''
            if hasattr(production, 'date_start') and production.date_start:
                date_prod = production.date_start.strftime('%Y-%m-%d %H:%M:%S')
            elif hasattr(production, 'date_planned_start') and production.date_planned_start:
                date_prod = production.date_planned_start.strftime('%Y-%m-%d %H:%M:%S')

            # Préparer les données JSON à envoyer
            data = {
                'reference': production.name,
                'product_to_produce': production.product_id.sudo().display_name,  # <-- sudo() ici aussi
                'qty_to_produce': production.product_qty,
                'bom_name': production.bom_id.sudo().display_name if production.bom_id else '',
                'product_uom': production.product_uom_id.sudo().name,
                'user_name': production.user_id.sudo().name,
                'company_name': production.company_id.sudo().name,
                'date': date_prod,
                'components': lines,
            }

            # Envoi vers le microservice Flask
            url = "https://xprinter.sysadaptpro.com/print_mo"
            headers = {
                'X-API-KEY': 'odoo1234',
                'Content-Type': 'application/json',
            }

            try:
                response = requests.post(url, json=data, headers=headers, timeout=10)
                if response.status_code == 200:
                    production.message_post(body="🖨️ Impression envoyée avec succès à XPrinter.")
                else:
                    production.message_post(body=f"⚠️ Erreur d’impression XPrinter : {response.text}")
            except Exception as e:
                production.message_post(body=f"❌ Impossible d’envoyer à l’imprimante : {str(e)}")
