# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError

IMPORT_CHINE_NAME = "IMPORT CHINE"
ALLOWED_EMAILS = {"micka@gmail.com", "nivo@mail.com"}  # autorisés hors IMPORT CHINE

class ProjectTask(models.Model):
    _inherit = "project.task"

    # -------- Helpers --------
    def _is_import_chine_id(self, project_id):
        if not project_id:
            return False
        proj = project_id if hasattr(project_id, "id") else self.env["project.project"].browse(project_id)
        return bool(proj.exists() and (proj.name or "").strip().lower() == IMPORT_CHINE_NAME.lower())

    def _user_allowed_for_other_projects(self):
        user = self.env.user
        email = (user.partner_id.email or user.login or "").strip().lower()
        return bool(user._is_superuser() or email in {e.lower() for e in ALLOWED_EMAILS})

    def _counts_for_ref(self, payref):
        """Retourne (ic_count, other_project_count, first_other_name) pour la ref."""
        if not payref:
            return 0, 0, ""
        tasks = self.search([("name", "=", payref)])
        ic_count = sum(1 for t in tasks if (t.project_id.name or "").strip().lower() == IMPORT_CHINE_NAME.lower())
        other_projects = {t.project_id.id: t.project_id.display_name
                          for t in tasks
                          if (t.project_id.name or "").strip().lower() != IMPORT_CHINE_NAME.lower()}
        other_count = len(other_projects)
        first_other_name = next(iter(other_projects.values()), "")
        return ic_count, other_count, first_other_name

    # -------- Règle de création depuis Facturation --------
    @api.model_create_multi
    def create(self, vals_list):
        """
        S’active SEULEMENT si context['from_invoice']=True (depuis Facturation).
        Règle : au maximum 2 tâches par référence :
          • 1 dans 'IMPORT CHINE' (IC) + 1 dans un autre projet.
          • Dans IC : pas de doublon IC (pour tout le monde).
          • Hors IC : réservé à Micka/Nivo (ou superuser), et une seule fois au total hors IC.
          • Si déjà 1 IC + 1 hors IC -> blocage partout.
        """
        if self.env.context.get("from_invoice"):
            for vals in vals_list:
                ref = (vals.get("name") or "").strip()
                pid = vals.get("project_id") or self.env.context.get("default_project_id")
                is_target_ic = self._is_import_chine_id(pid)

                ic_count, other_count, first_other_name = self._counts_for_ref(ref)

                # Cap global atteint : déjà 1 en IC + 1 hors IC -> plus aucune création
                if ref and ic_count >= 1 and other_count >= 1:
                    raise UserError(
                        _("La référence de paiement '%s' existe déjà dans 'IMPORT CHINE' et dans le projet '%s'. Nouvelle création interdite.")
                        % (ref, first_other_name)
                    )

                if is_target_ic:
                    # IC : autorisé pour tout le monde mais sans doublon IC
                    if ref and ic_count >= 1:
                        raise UserError(_("Cette référence existe déjà dans le projet 'IMPORT CHINE'."))
                else:
                    # Hors IC : seulement Micka/Nivo (ou superuser)
                    if not self._user_allowed_for_other_projects():
                        raise UserError(_("Vous n'êtes pas autorisé à créer une tâche dans ce projet. Utilisez le projet 'IMPORT CHINE'."))

                    # Une seule création hors IC au total
                    if ref and other_count >= 1:
                        raise UserError(
                            _("La référence de paiement '%s' a déjà été créée dans le projet '%s' (hors 'IMPORT CHINE'). Une seule création hors 'IMPORT CHINE' est autorisée.")
                            % (ref, first_other_name)
                        )
        return super().create(vals_list)
