# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = "project.task"

    # Saisi libre (numéro de facture, code suivi, etc.) — sert à tenter d'identifier la facture
    invoice_ref = fields.Char(string="Référence facture")

    # Devis lié (si déjà créé ou détecté)
    sale_order_id = fields.Many2one(
        "sale.order", string="Devis lié", readonly=True, copy=False
    )

    # Étape éligible (vrai si la tâche est dans une des étapes COLIS RECUE ...)
    is_colis_recue_mada = fields.Boolean(
        string="Étape éligible pour devis",
        compute="_compute_is_colis_recue_mada",
        store=False,
    )

    # Détection d'un devis existant (client_order_ref = nom de la tâche OU invoice_ref)
    existing_sale_id = fields.Many2one(
        "sale.order",
        string="Devis existant (même référence)",
        compute="_compute_existing_sale_id",
        store=False,
    )

    # --------------------------
    # Computes
    # --------------------------
    @api.depends("stage_id")
    def _compute_is_colis_recue_mada(self):
        allowed = {
            "COLIS RECUE MADA",
            "COLIS RECUE FIANARANTSOA",
            "COLIS RECUE ANTSIRABE",
            "COLIS RECUE TAMATAVE",
            "COLIS RECUE NOSY BE",
            "COLIS RECUE MAHAJANGA",
        }
        for task in self:
            name = (task.stage_id.name or "").strip().upper() if task.stage_id else ""
            task.is_colis_recue_mada = name in allowed

    @api.depends("invoice_ref", "name")
    def _compute_existing_sale_id(self):
        SaleOrder = self.env["sale.order"].sudo()
        for task in self:
            task.existing_sale_id = False
            refs = []
            if task.name:
                refs.append(task.name.strip())
            if task.invoice_ref:
                refs.append(task.invoice_ref.strip())
            if not refs:
                continue
            so = SaleOrder.search(
                [("client_order_ref", "in", refs), ("state", "in", ["draft", "sent", "sale", "done"])],
                order="id desc",
                limit=1,
            )
            task.existing_sale_id = so

    # --------------------------
    # Helpers
    # --------------------------
    def _find_invoice_from_ref(self, ref_text):
        """Tente de retrouver une facture depuis un texte (numéro, payment_reference, ref).
        Renvoie un recordset (peut être vide).
        """
        self.ensure_one()
        if not ref_text:
            return self.env["account.move"]
        Move = self.env["account.move"]
        domain_base = [("move_type", "in", ["out_invoice", "out_refund"])]
        ref = ref_text.strip()

        # exact
        inv = Move.search(domain_base + [("name", "=", ref)], limit=1)
        if inv:
            return inv
        inv = Move.search(domain_base + [("payment_reference", "=", ref)], limit=1)
        if inv:
            return inv
        inv = Move.search(domain_base + [("ref", "=", ref)], limit=1)
        if inv:
            return inv

        # ilike (IMPORTANT: '|' séparés dans la liste)
        inv = Move.search(
            domain_base + [
                "|", "|",
                ("name", "ilike", ref),
                ("payment_reference", "ilike", ref),
                ("ref", "ilike", ref),
            ],
            order="state desc, invoice_date desc, id desc",
            limit=1,
        )
        return inv

    # --------------------------
    # Actions
    # --------------------------
    def action_create_quotation_from_invoice_ref(self):
        """Crée ou lie un devis.
        Règles:
          - Bouton actif si étape ∈ {COLIS RECUE MADA, FIANARANTSOA, ANTSIRABE, TAMATAVE, NOSY BE, MAHAJANGA}
          - client_order_ref du devis = NOM DE LA TÂCHE
          - Anti-doublons sur client_order_ref (nom de la tâche) et invoice_ref
          - Si aucune facture n'est trouvée, on utilise task.partner_id comme client
        """
        SaleOrder = self.env["sale.order"]

        for task in self:
            if not task.is_colis_recue_mada:
                raise UserError(_("Le bouton est disponible uniquement pour les étapes : "
                                  "COLIS RECUE MADA, COLIS RECUE FIANARANTSOA, COLIS RECUE ANTSIRABE, "
                                  "COLIS RECUE TAMATAVE, COLIS RECUE NOSY BE, COLIS RECUE MAHAJANGA."))

            # 1) Déjà lié
            if task.sale_order_id:
                action = self.env.ref("sale.action_quotations_with_onboarding").read()[0]
                action.update({"view_mode": "form", "res_id": task.sale_order_id.id})
                return action

            # 2) Existe déjà (vérifie nom de tâche + invoice_ref)
            name_ref = (task.name or "").strip()
            inv_ref = (task.invoice_ref or "").strip()
            search_refs = [r for r in [name_ref, inv_ref] if r]
            if search_refs:
                already = SaleOrder.search(
                    [("client_order_ref", "in", search_refs), ("state", "in", ["draft", "sent", "sale", "done"])],
                    limit=1,
                )
                if already:
                    task.sale_order_id = already.id
                    task.message_post(body=_("Devis existant détecté (référence: %s) — lien automatique effectué.")
                                      % already.client_order_ref)
                    action = self.env.ref("sale.action_quotations_with_onboarding").read()[0]
                    action.update({"view_mode": "form", "res_id": already.id})
                    return action

            # 3) Identifier le client
            invoice = self.env["account.move"]
            if inv_ref:
                invoice = task._find_invoice_from_ref(inv_ref) or self.env["account.move"]

            partner = invoice.partner_id if invoice and invoice.partner_id else task.partner_id
            if not partner:
                raise UserError(_("Aucun client trouvé. Veuillez renseigner le 'Client' sur la tâche ou une facture valide dans 'Référence facture'."))

            company = task.company_id or partner.company_id or self.env.company

            # 4) Construire la note
            note_text = _("Devis créé depuis la tâche %(task)s") % {"task": task.display_name}
            if invoice:
                note_text += _("\nFacture d'origine: %(inv)s") % {"inv": invoice.display_name}

            # 5) Création du devis (sans lignes)
            client_order_ref = name_ref or _("Tâche %s") % task.id
            sale = SaleOrder.create({
                "partner_id": partner.id,
                "company_id": company.id,
                "origin": (invoice.name or task.name or _("Tâche %s") % task.id) if invoice else (task.name or _("Tâche %s") % task.id),
                "client_order_ref": client_order_ref,  # = nom de la tâche
                "note": note_text,
            })

            # 6) Lier à la tâche
            task.sale_order_id = sale.id

        action = self.env.ref("sale.action_quotations_with_onboarding").read()[0]
        if len(self) == 1 and self.sale_order_id:
            action.update({"view_mode": "form", "res_id": self.sale_order_id.id})
        return action
