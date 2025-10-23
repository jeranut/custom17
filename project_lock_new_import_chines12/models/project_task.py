# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError

IMPORT_CHINE_NAME = "IMPORT CHINE"
ALLOWED_EMAIL = "micka@gmail.com"

class ProjectTask(models.Model):
    _inherit = "project.task"

    # ---------- Helpers ----------
    def _is_import_chine_id(self, project_id):
        if not project_id:
            return False
        proj = project_id if isinstance(project_id, models.BaseModel) else self.env["project.project"].browse(project_id)
        return bool(proj.exists() and (proj.name or "").strip().lower() == IMPORT_CHINE_NAME.lower())

    def _in_import_chine(self):
        for t in self:
            if self._is_import_chine_id(t.project_id.id):
                return True
        return False

    def _is_allowed_user(self):
        user = self.env.user
        email = (user.partner_id.email or user.login or "").strip().lower()
        return bool(user._is_superuser() or email == ALLOWED_EMAIL.lower())

    # ---------- Verrous serveur ----------
    def unlink(self):
        # Suppression toujours réservée à micka (ou superuser)
        if self._in_import_chine() and not self._is_allowed_user():
            raise UserError(_("Suppression interdite : seul %s peut supprimer des tâches du projet 'IMPORT CHINE'.") % ALLOWED_EMAIL)
        return super().unlink()

    def write(self, vals):
        # ➜ Afficher seulement : "L’archivage des tâches est interdit."
        if "active" in vals and self._in_import_chine() and not self._is_allowed_user():
            raise UserError(_("L’archivage des tâches est interdit."))
        return super().write(vals)

    def action_archive(self):
        if self._in_import_chine() and not self._is_allowed_user():
            raise UserError(_("L’archivage des tâches est interdit."))
        return super().action_archive()

    def action_unarchive(self):
        if self._in_import_chine() and not self._is_allowed_user():
            raise UserError(_("L’archivage des tâches est interdit."))
        return super().action_unarchive()
