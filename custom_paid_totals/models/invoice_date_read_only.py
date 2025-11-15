from odoo import models, fields, api, _
from datetime import date


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_date = fields.Date(
        string="Date de la facture",
        default=lambda self: date.today(),
        readonly=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMove, self).default_get(fields_list)
        res['invoice_date'] = date.today()
        return res
