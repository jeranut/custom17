from odoo import models, fields, api

class AccountDailyBalance(models.Model):
    _name = 'account.daily.balance'
    _description = 'Rapport journalier Débit/Crédit'
    _rec_name = 'date'

    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    total_debit = fields.Float(string='Total Débit', readonly=True)
    total_credit = fields.Float(string='Total Crédit', readonly=True)

    line_ids = fields.One2many('account.daily.balance.line', 'balance_id', string='Détails')

    _sql_constraints = [
        ('unique_date', 'unique(date)', 'Une seule ligne est autorisée par jour.')
    ]

    def action_update_totals(self):
        for record in self:
            # On vide les anciennes lignes
            record.line_ids.unlink()

            total_credit = 0
            total_debit = 0

            # ✅ Factures clients (out_invoice) — payées
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

            # ✅ Factures fournisseurs (in_invoice) — payées
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

            # ✅ Dépenses RH (hr.expense) validées
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

            # ✅ Écriture des totaux
            record.write({
                'total_debit': total_debit,
                'total_credit': total_credit,
            })


class AccountDailyBalanceLine(models.Model):
    _name = 'account.daily.balance.line'
    _description = 'Ligne du rapport journalier Débit/Crédit'

    balance_id = fields.Many2one('account.daily.balance', string='Balance', ondelete='cascade')
    reference = fields.Char(string='Référence')
    libelle = fields.Char(string='Libellé')
    debit = fields.Float(string='Débit')
    credit = fields.Float(string='Crédit')
