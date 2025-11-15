from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class AccountDailyBalance(models.Model):
    _name = 'account.daily.balance'
    _description = 'Rapport journalier Débit/Crédit'
    _rec_name = 'date'

    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    total_debit = fields.Float(string='Total Débit', readonly=True)
    total_credit = fields.Float(string='Total Crédit', readonly=True)
    ancien_solde = fields.Float(string='Ancien solde')
    nouveau_solde = fields.Float(string='Nouveau solde', readonly=True)
    show_lines = fields.Boolean(string='Afficher les lignes', default=False)

    line_ids = fields.One2many('account.daily.balance.line', 'balance_id', string='Détails')

    _sql_constraints = [
        ('unique_date', 'unique(date)', 'Une seule ligne est autorisée par jour.')
    ]

    # -------------------------------------------------------------------------
    # Vérifie à l'ouverture du formulaire (bouton "Nouveau")
    # Si un bilan du jour existe déjà → empêche la création
    # -------------------------------------------------------------------------
    @api.model
    def default_get(self, fields_list):
        today = fields.Date.context_today(self)
        last_balance = self.search([], order="date desc", limit=1)

        # 🔒 Empêche la création si un enregistrement du jour existe déjà
        if last_balance and last_balance.date == today:
            raise UserError(_(
                "⚠️ L’exercice du jour a déjà été créé.\n"
                "Veuillez ouvrir l’enregistrement du jour dans la liste existante."
            ))

        # 🟢 Sinon, comportement normal (création autorisée)
        return super(AccountDailyBalance, self).default_get(fields_list)

    # -------------------------------------------------------------------------
    # Détermine automatiquement l'ancien solde au moment de la création
    # -------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        """Ajout de la vérification : si un bilan du jour existe déjà, bloquer."""
        today = fields.Date.context_today(self)
        last_balance = self.search([], order="date desc", limit=1)
        if last_balance and last_balance.date == today:
            raise UserError(_(
                "⚠️ L’exercice du jour a déjà été créé.\n"
                "Veuillez ouvrir l’enregistrement du jour dans la liste existante."
            ))

        # --- Code d’origine inchangé ci-dessous ---
        date_record = vals.get('date')
        if date_record:
            if isinstance(date_record, str):
                date_record = fields.Date.from_string(date_record)
            previous_day = date_record - timedelta(days=1)
            previous_balance = self.search([('date', '=', previous_day)], limit=1)

            if previous_balance and previous_balance.nouveau_solde:
                vals['ancien_solde'] = previous_balance.nouveau_solde
            else:
                # Premier jour → solde à saisir via wizard
                vals['ancien_solde'] = 0.0
        return super().create(vals)

    # -------------------------------------------------------------------------
    # Bouton : Mettre à jour les totaux
    # -------------------------------------------------------------------------
    def action_update_totals(self):
        for record in self:
            today = fields.Date.context_today(self)

            # 🚫 Empêche la mise à jour pour une date future
            if record.date > today:
                raise UserError(_("Veuillez sélectionner la date du jour avant de mettre à jour les totaux."))

            # 🔒 Empêche la modification des jours passés
            if record.date < today:
                raise UserError(_("Impossible de recalculer une journée passée."))

            # 🔁 Recherche du solde précédent
            previous_day = record.date - timedelta(days=1)
            previous_balance = self.search([('date', '=', previous_day)], limit=1)

            if previous_balance and previous_balance.nouveau_solde:
                record.ancien_solde = previous_balance.nouveau_solde
            elif not record.ancien_solde or record.ancien_solde == 0:
                # 🔔 Ouvre le wizard si aucun solde précédent
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Saisir le solde initial'),
                    'res_model': 'account.daily.balance.init.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_balance_id': record.id},
                }

            # 🔄 Efface les anciennes lignes avant recalcul
            record.line_ids.unlink()

            total_credit = 0
            total_debit = 0

            # ✅ Factures clients payées
            client_invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '=', 'paid'),
                ('invoice_date', '=', record.date),
                ('state', '=', 'posted')
            ])
            for inv in client_invoices:
                self.env['account.daily.balance.line'].create({
                    'balance_id': record.id,
                    'reference': inv.name,
                    'libelle': inv.invoice_origin or inv.ref or 'Facture client',
                    'debit': inv.amount_total,
                    'credit': 0.0,
                })
            total_credit += sum(client_invoices.mapped('amount_total'))

            # ✅ Factures fournisseurs payées
            vendor_bills = self.env['account.move'].search([
                ('move_type', '=', 'in_invoice'),
                ('payment_state', '=', 'paid'),
                ('invoice_date', '=', record.date),
                ('state', '=', 'posted')
            ])
            for bill in vendor_bills:
                self.env['account.daily.balance.line'].create({
                    'balance_id': record.id,
                    'reference': bill.name,
                    'libelle': bill.ref or 'Facture fournisseur',
                    'debit': 0.0,
                    'credit': bill.amount_total,
                })
            total_debit += sum(vendor_bills.mapped('amount_total'))

            # ✅ Dépenses RH validées
            hr_expenses = self.env['hr.expense'].search([
                ('state', '=', 'done'),
                ('date', '=', record.date)
            ])
            for exp in hr_expenses:
                self.env['account.daily.balance.line'].create({
                    'balance_id': record.id,
                    'reference': exp.name,
                    'libelle': 'Dépense RH',
                    'debit': 0.0,
                    'credit': exp.total_amount,
                })
            total_debit += sum(hr_expenses.mapped('total_amount'))

            # ✅ Calcul du nouveau solde
            nouveau_solde = record.ancien_solde + (total_credit - total_debit)

            record.write({
                'total_debit': total_debit,
                'total_credit': total_credit,
                'nouveau_solde': nouveau_solde,
                'show_lines': True,
            })


# -------------------------------------------------------------------------
# Lignes de détail
# -------------------------------------------------------------------------
class AccountDailyBalanceLine(models.Model):
    _name = 'account.daily.balance.line'
    _description = 'Ligne du rapport journalier Débit/Crédit'

    balance_id = fields.Many2one('account.daily.balance', string='Balance', ondelete='cascade')
    reference = fields.Char(string='Référence')
    libelle = fields.Char(string='Libellé')
    debit = fields.Float(string='Débit')
    credit = fields.Float(string='Crédit')


# -------------------------------------------------------------------------
# Wizard pour initialiser le solde de départ
# -------------------------------------------------------------------------
class AccountDailyBalanceInitWizard(models.TransientModel):
    _name = 'account.daily.balance.init.wizard'
    _description = 'Wizard pour initialiser le solde'

    balance_id = fields.Many2one('account.daily.balance', string='Balance liée')
    initial_balance = fields.Float(string='Solde initial', required=True)

    def action_confirm(self):
        """Valide le solde initial et relance le calcul"""
        if not self.balance_id:
            raise UserError(_("Aucune balance liée au wizard."))

        self.balance_id.ancien_solde = self.initial_balance
        self.balance_id.action_update_totals()
        return {'type': 'ir.actions.act_window_close'}
