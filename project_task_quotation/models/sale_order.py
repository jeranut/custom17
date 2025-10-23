# -*- coding: utf-8 -*-
from odoo import models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        """Forcer payment_reference = client_order_ref lors de la génération de la facture."""
        self.ensure_one()
        vals = super()._prepare_invoice()
        if self.client_order_ref:
            vals["payment_reference"] = self.client_order_ref
        return vals
