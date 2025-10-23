# -*- coding: utf-8 -*-
from odoo import api, fields, models

IMPORT_CHINE_NAME = "IMPORT CHINE"
ALLOWED_EMAIL = "micka@gmail.com"

class ProjectProject(models.Model):
    _inherit = "project.project"

    def _should_lock_create(self):
        self.ensure_one()
        # Verrouiller si le nom du projet (insensible à la casse) est "IMPORT CHINE"
        return (self.name or "").strip().lower() == IMPORT_CHINE_NAME.lower()

    def _is_allowed_user(self):
        user = self.env.user
        email = (user.partner_id.email or user.login or "").strip().lower()
        return bool(user._is_superuser() or email == ALLOWED_EMAIL.lower())

    def _lock_create_in_action(self, action):
        """Force create=False/quick_create=False/kanban_create=False; cache 'Supprimer' si non autorisé."""
        if not action:
            return action
        ctx = action.get("context") or {}
        if isinstance(ctx, str):
            try:
                from ast import literal_eval
                ctx = literal_eval(ctx)
            except Exception:
                ctx = {}
        ctx.update({
            "create": False,
            "quick_create": False,
            "kanban_create": False,
        })
        # cacher 'Supprimer' dans la barre d'actions pour les non-autorisés
        if not self._is_allowed_user():
            ctx["delete"] = False
        action["context"] = ctx
        return action

    def action_view_tasks(self):
        action = super().action_view_tasks()
        if len(self) == 1 and self._should_lock_create():
            action = self._lock_create_in_action(action)
        return action

    def action_view_tasks_all(self):
        action = super().action_view_tasks_all()
        if len(self) == 1 and self._should_lock_create():
            action = self._lock_create_in_action(action)
        return action
