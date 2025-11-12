from odoo import models, api

class PosFolioFilter(models.AbstractModel):
    _name = "pos.folio.filter"
    _description = "Helper to open hotel folio from POS"

    @api.model
    def get_folio_action(self):
        """Retourne l’action affichant tous les folios existants"""
        action = self.env.ref("custom_pos_screen.action_folio_from_pos").read()[0]
        # Tu peux ici filtrer (ex : folios du jour)
        # folio_ids = self.env["hotel.folio"].search([]).ids
        # action["domain"] = [("id", "in", folio_ids)]
        return action
