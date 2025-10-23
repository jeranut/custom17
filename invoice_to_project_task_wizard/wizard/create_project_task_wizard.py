# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import html_escape


class InvoiceCreateProjectTaskWizard(models.TransientModel):
    _name = "invoice.create.project.task.wizard"
    _description = "Wizard: sélectionner le projet pour créer la tâche"

    project_id = fields.Many2one(
        "project.project", string="Projet", required=True,
        help="Projet cible où la tâche sera créée (étape 'COLIS EN ATTENTE')."
    )

    # ---------- helpers ----------
    def _ensure_stage_colis_attente(self, project):
        Stage = self.env["project.task.type"]
        stage = Stage.search([
            "&", ("name", "ilike", "COLIS EN ATTENTE"),
            "|", ("project_ids", "=", False), ("project_ids", "in", project.id)
        ], limit=1)
        if not stage:
            stage = Stage.create({"name": "COLIS EN ATTENTE", "project_ids": [(4, project.id)]})
        return stage

    @staticmethod
    def _fmt_money(currency, amount):
        symbol = currency.symbol or ""
        return f"{symbol} {amount:,.2f}".replace(",", " ")

    def _build_task_description_html(self, move, labels):
        partner = move.partner_id
        title = html_escape(_("Créée depuis la facture %s") % (move.name or move.ref or ""))
        client = html_escape(partner.display_name or "")
        ville = html_escape(partner.city or "")
        phone = html_escape(partner.phone or partner.mobile or "")
        payref = html_escape(move.payment_reference or move.ref or "")
        currency = move.currency_id
        currency_text = html_escape(f"{currency.name} ({currency.symbol or ''})")
        total_text = html_escape(self._fmt_money(currency, move.amount_total))
        lis = "".join(f"<li>{html_escape(l or '')}</li>" for l in labels if l)
        return f"""
<div>
  <h4>{title}</h4>
  <table style="border-collapse:collapse;">
    <tr><td style="width:160px;"><b>{html_escape(_('Client'))}</b></td><td>{client}</td></tr>
    <tr><td><b>{html_escape(_('Ville'))}</b></td><td>{ville}</td></tr>
    <tr><td><b>{html_escape(_('Téléphone'))}</b></td><td>{phone}</td></tr>
    <tr><td><b>{html_escape(_('Réf. paiement'))}</b></td><td>{payref}</td></tr>
    <tr><td><b>{html_escape(_('Devise'))}</b></td><td>{currency_text}</td></tr>
    <tr><td><b>{html_escape(_('Total TTC'))}</b></td><td>{total_text}</td></tr>
  </table>
  <h5 style="margin-top:10px;">{html_escape(_('Libellés de facture'))}</h5>
  <ul style="margin:0 0 6px 18px;">{lis or '<li>-</li>'}</ul>
</div>
""".strip()

    def action_confirm(self):
        self.ensure_one()
        project = self.project_id
        stage = self._ensure_stage_colis_attente(project)

        Task = self.env["project.task"].with_context(from_invoice=True)  # active les règles serveur
        Move = self.env["account.move"]
        moves = Move.browse(self.env.context.get("active_ids", []))

        for move in moves:
            # Facture client/avoir + postée
            if move.move_type not in ("out_invoice", "out_refund") or move.state != "posted":
                continue

            payref = (move.payment_reference or "").strip()
            if not payref:
                raise UserError(_("Référence de paiement manquante.\nRenseignez 'Réf. paiement' sur la facture."))

            # Unicité vérifiée SEULEMENT dans le projet choisi
            if Task.search_count([("project_id", "=", project.id), ("name", "=", payref)]):
                raise UserError(_("La référence de paiement '%s' existe déjà comme nom de tâche dans le projet '%s'.")
                                % (payref, project.display_name))

            # Description HTML
            lines = move.invoice_line_ids.filtered(lambda l: not l.display_type)
            labels = [l.name for l in lines if l.name] or [payref]
            description_html = self._build_task_description_html(move, labels)

            # Valeurs de création
            vals = {
                "name": payref,                  # nom = référence paiement
                "invoice_ref": payref,           # <-- ICI: on renseigne le champ existant
                "project_id": project.id,
                "description": description_html,
                "partner_id": move.partner_id.id or False,
                "stage_id": stage.id,
            }

            # Tag auto = ville du client si projet "IMPORT CHINE"
            if (project.name or "").strip().lower() == "import chine":
                city = (move.partner_id.city or "").strip()
                if city:
                    Tags = self.env["project.tags"]
                    tag = Tags.search([("name", "=", city)], limit=1)
                    if not tag:
                        tag = Tags.create({"name": city})
                    vals["tag_ids"] = [(6, 0, [tag.id])]

            Task.create(vals)

        return {"type": "ir.actions.act_window_close"}
