# -*- coding: utf-8 -*-
from odoo import models, _

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_open_task_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Créer tâche projet"),
            "res_model": "invoice.create.project.task.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": "account.move",
                "active_ids": self.ids,
            },
        }
