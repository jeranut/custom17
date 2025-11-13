from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta, date

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

    @api.model
    def create(self, vals):
        """Détermination automatique de l'ancien solde au moment de la création"""
        date_record = vals.get('date')
        if date_record:
            # convertir str en date si nécessaire
            if isinstance(date_record, str):
                date_record = fields.Date.from_string(date_record)
            previous_day = date_record - timedelta(days=1)
            previous_balance = self.search([('date', '=', previous_day)], limit=1)

            if previous_balance and previous_balance.nouveau_solde:
                vals['ancien_solde'] = previous_balance.nouveau_solde
            else:
                # aucun solde précédent → popup à saisir manuellement
                vals['ancien_solde'] = 0.0
        return super(AccountDailyBalance, self).create(vals)

    def action_update_totals(self):
        for record in self:
            today = fields.Date.context_today(self)

            # Si la date sélectionnée < aujourd’hui, on bloque la mise à jour
            if record.date < today:
                raise UserError(_("Impossible de recalculer une journée passée. Les anciens soldes sont figés."))

            # Récupération du solde du jour précédent
            previous_day = record.date - timedelta(days=1)
            previous_balance = self.search([('date', '=', previous_day)], limit=1)
            if previous_balance and previous_balance.nouveau_solde:
                record.ancien_solde = previous_balance.nouveau_solde
            elif not record.ancien_solde:
                # si ancien_solde encore vide → popup manuel
                raise UserError(_(
                    "Aucun solde précédent trouvé.\nVeuillez entrer manuellement le solde de départ dans le champ 'Ancien solde'."
                ))

            # Efface les anciennes lignes
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
                'show_lines': True,  # affiche le tree après clic
            })


class AccountDailyBalanceLine(models.Model):
    _name = 'account.daily.balance.line'
    _description = 'Ligne du rapport journalier Débit/Crédit'

    balance_id = fields.Many2one('account.daily.balance', string='Balance', ondelete='cascade')
    reference = fields.Char(string='Référence')
    libelle = fields.Char(string='Libellé')
    debit = fields.Float(string='Débit')
    credit = fields.Float(string='Crédit')
