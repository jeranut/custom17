from odoo import models, fields

class DateLine(models.Model):
    _name = "date.line"
    _description = "Jour de l'intervalle"

    parent_id = fields.Many2one("my.model", string="Intervalle", ondelete="cascade")
    date = fields.Date(string="Date", required=True)
