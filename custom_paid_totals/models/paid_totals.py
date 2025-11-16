from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class AccountDailyBalance(models.Model):
    _name = 'account.daily.balance'
    _description = 'Rapport journalier Débit/Crédit'
    _rec_name = 'date'

    date = fields.Date(string='Date', required=True, default=fields.Date.context_today, readonly=True)
    total_debit = fields.Float(string='Total Débit', readonly=True)
    total_credit = fields.Float(string='Total Crédit', readonly=True)
    ancien_solde = fields.Float(string='Ancien solde', readonly=True)
    nouveau_solde = fields.Float(string='Nouveau solde', readonly=True)
    show_lines = fields.Boolean(string='Afficher les lignes', default=False)

    line_ids = fields.One2many('account.daily.balance.line', 'balance_id', string='Détails')

    _sql_constraints = [
        ('unique_date', 'unique(date)', 'Une seule ligne est autorisée par jour.')
    ]

    @api.model
    def default_get(self, fields_list):
        today = fields.Date.context_today(self)
        last_balance = self.search([], order="date desc", limit=1)

        if last_balance and last_balance.date == today:
            raise UserError(_(
                "L’exercice du jour a déjà été créé.\n"
                "Veuillez ouvrir l’enregistrement du jour dans la liste existante."
            ))

        return super(AccountDailyBalance, self).default_get(fields_list)

    @api.model
    def create(self, vals):
        today = fields.Date.context_today(self)
        last_balance = self.search([], order="date desc", limit=1)
        if last_balance and last_balance.date == today:
            raise UserError(_(
                "L’exercice du jour a déjà été créé.\n"
                "Veuillez ouvrir l’enregistrement du jour dans la liste existante."
            ))

        date_record = vals.get('date')
        if date_record:
            if isinstance(date_record, str):
                date_record = fields.Date.from_string(date_record)
            previous_day = date_record - timedelta(days=1)
            previous_balance = self.search([('date', '=', previous_day)], limit=1)

            if previous_balance and previous_balance.nouveau_solde:
                vals['ancien_solde'] = previous_balance.nouveau_solde
            else:
                vals['ancien_solde'] = 0.0

        return super().create(vals)

    def action_update_totals(self):
        for record in self:
            today = fields.Date.context_today(self)

            if record.date < today:
                raise UserError(_("Impossible de recalculer une journée passée."))
            if record.date > today:
                raise UserError(_("Veuillez sélectionner la date du jour pour effectuer le calcul."))

            previous_day = record.date - timedelta(days=1)
            previous_balance = self.search([('date', '=', previous_day)], limit=1)

            if previous_balance and previous_balance.nouveau_solde:
                record.ancien_solde = previous_balance.nouveau_solde
            elif not record.ancien_solde or record.ancien_solde == 0:
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Saisir le solde initial'),
                    'res_model': 'account.daily.balance.init.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_balance_id': record.id},
                }

            total_credit = 0
            total_debit = 0

            # Factures clients CASH uniquement
            client_invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '=', 'paid'),
                ('invoice_date', '=', record.date),
                ('state', '=', 'posted')
            ])
            for inv in client_invoices:
                payments = inv._get_reconciled_payments()
                payment = payments[0] if payments else False

                if not payment or payment.journal_id.type != "cash":
                    continue

                existing = self.env['account.daily.balance.line'].search([
                    ('balance_id', '=', record.id),
                    ('reference', '=', inv.name)
                ], limit=1)

                if existing:
                    existing.write({
                        'libelle': inv.journal_label,
                        'payment': "cash",
                        'debit': 0.0,
                        'credit': inv.amount_total,
                    })
                else:
                    self.env['account.daily.balance.line'].create({
                        'balance_id': record.id,
                        'reference': inv.name,
                        'libelle': inv.journal_label,
                        'payment': "cash",
                        'debit': 0.0,
                        'credit': inv.amount_total,
                    })

            total_credit += sum([inv.amount_total for inv in client_invoices if
                                 inv._get_reconciled_payments() and inv._get_reconciled_payments()[
                                     0].journal_id.type == "cash"])

            # Factures fournisseurs CASH uniquement
            vendor_bills = self.env['account.move'].search([
                ('move_type', '=', 'in_invoice'),
                ('payment_state', '=', 'paid'),
                ('invoice_date', '=', record.date),
                ('state', '=', 'posted')
            ])
            for bill in vendor_bills:
                payments = bill._get_reconciled_payments()
                payment = payments[0] if payments else False

                if not payment or payment.journal_id.type != "cash":
                    continue

                existing = self.env['account.daily.balance.line'].search([
                    ('balance_id', '=', record.id),
                    ('reference', '=', bill.name)
                ], limit=1)

                if existing:
                    existing.write({
                        'libelle': bill.journal_label,
                        'payment': "cash",
                        'debit': bill.amount_total,
                        'credit': 0.0,
                    })
                else:
                    self.env['account.daily.balance.line'].create({
                        'balance_id': record.id,
                        'reference': bill.name,
                        'libelle': bill.journal_label,
                        'payment': "cash",
                        'debit': bill.amount_total,
                        'credit': 0.0,
                    })

            total_debit += sum([bill.amount_total for bill in vendor_bills if
                                bill._get_reconciled_payments() and bill._get_reconciled_payments()[
                                    0].journal_id.type == "cash"])

            # Dépenses RH
            hr_expenses = self.env['hr.expense'].search([
                ('state', '=', 'done'),
                ('date', '=', record.date)
            ])
            for exp in hr_expenses:
                existing = self.env['account.daily.balance.line'].search([
                    ('balance_id', '=', record.id),
                    ('reference', '=', exp.name)
                ], limit=1)

                if existing:
                    existing.write({
                        'libelle': 'Dépense RH',
                        'payment': '',
                        'debit': exp.total_amount,
                        'credit': 0.0,
                    })
                else:
                    self.env['account.daily.balance.line'].create({
                        'balance_id': record.id,
                        'reference': exp.name,
                        'libelle': 'Dépense RH',
                        'payment': '',
                        'debit': exp.total_amount,
                        'credit': 0.0,
                    })

            total_debit += sum(hr_expenses.mapped('total_amount'))

            # recalcul des totaux
            total_credit = sum(record.line_ids.mapped('credit'))
            total_debit = sum(record.line_ids.mapped('debit'))

            nouveau_solde = record.ancien_solde + (total_credit - total_debit)

            record.write({
                'total_debit': total_debit,
                'total_credit': total_credit,
                'nouveau_solde': nouveau_solde,
                'show_lines': True,
            })

    def action_update_totals_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Wizard Totaux'),
            'res_model': 'update.totals.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_balance_id': self.id},
        }


class UpdateTotalsWizard(models.TransientModel):
    _name = 'update.totals.wizard'
    _description = 'Wizard Mettre à jour les totaux'

    balance_id = fields.Many2one('account.daily.balance', string='Balance liée')
    recette = fields.Float(string="Montant RECETTE", required=True)

    def action_confirm(self):
        self.ensure_one()

        if not self.balance_id:
            raise UserError(_("Aucune balance n'est liée au wizard."))

        if self.recette <= 0:
            raise UserError(_("Veuillez saisir un montant supérieur à 0."))

        from datetime import datetime
        current_year = datetime.now().year

        last_line = self.env['account.daily.balance.line'].search(
            [('reference', 'like', f"REC/{current_year}/%")],
            order="reference desc",
            limit=1
        )

        if last_line:
            last_number = int(last_line.reference.split('/')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        new_ref = "REC/%s/%05d" % (current_year, new_number)

        self.env['account.daily.balance.line'].create({
            'balance_id': self.balance_id.id,
            'reference': new_ref,
            'libelle': 'RECETTE',
            'payment': 'cash',
            'debit': 0.0,
            'credit': self.recette,
        })

        self.balance_id.action_update_totals()

        return {'type': 'ir.actions.act_window_close'}


class AccountDailyBalanceLine(models.Model):
    _name = 'account.daily.balance.line'
    _description = 'Ligne du rapport journalier Débit/Crédit'
    _order = 'id asc'
    _rec_name = 'reference'

    balance_id = fields.Many2one('account.daily.balance', string='Balance', ondelete='cascade')
    reference = fields.Char(string='REFERENCE FACTURE')
    libelle = fields.Char(string='LIBELLE')
    payment = fields.Char(string='PAYMENT')
    debit = fields.Float(string='DEBIT')
    credit = fields.Float(string='CREDIT')
    regule_badge = fields.Char(string="Badge", compute="_compute_regule_badge", store=True)
    origin_line_id = fields.Many2one(
        'account.daily.balance.line',
        string="Ligne d'origine",
        readonly=True
    )

    @api.depends('balance_id.line_ids.origin_line_id', 'balance_id.line_ids.libelle')
    def _compute_regule_badge(self):
        for line in self:
            # S'il s'agit d'une ligne REGULE elle-même → pas de badge
            if line.libelle == 'REGULE':
                line.regule_badge = ''
                continue

            # Compter les régules liées à cette ligne
            regulated = self.env['account.daily.balance.line'].search_count([
                ('origin_line_id', '=', line.id),
                ('libelle', '=', 'REGULE')
            ])

            line.regule_badge = "REGULE" if regulated >= 1 else ""


class AccountDailyBalanceInitWizard(models.TransientModel):
    _name = 'account.daily.balance.init.wizard'
    _description = 'Wizard pour initialiser le solde'

    balance_id = fields.Many2one('account.daily.balance', string='Balance liée')
    initial_balance = fields.Float(string='Solde initial', required=True)

    def action_confirm(self):
        if not self.balance_id:
            raise UserError(_("Aucune balance liée au wizard."))

        self.balance_id.ancien_solde = self.initial_balance
        self.balance_id.action_update_totals()
        return {'type': 'ir.actions.act_window_close'}


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    journal_type = fields.Char(string="Journal Type", readonly=True)

    @api.onchange('journal_id')
    def _onchange_journal_type(self):
        self.journal_type = self.journal_id.type if self.journal_id else ""

    def action_create_payments(self):
        payments = super(AccountPaymentRegister, self).action_create_payments()

        if self.journal_id.type == "cash":
            today = fields.Date.context_today(self.env['account.daily.balance'])
            balance = self.env['account.daily.balance'].search([('date', '=', today)], limit=1)

            if not balance:
                balance = self.env['account.daily.balance'].create({'date': today})

            balance.action_update_totals()

        return payments


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    def action_sheet_move_create(self):
        res = super(HrExpenseSheet, self).action_sheet_move_create()

        for sheet in self:
            today = fields.Date.context_today(self.env['account.daily.balance'])
            balance = self.env['account.daily.balance'].search([('date', '=', today)], limit=1)

            if not balance:
                balance = self.env['account.daily.balance'].create({'date': today})

            balance.action_update_totals()

        return res


# ------------------------------------------------------
# 🔹 Wizard Régulation
# ------------------------------------------------------
class ReguleWizard(models.TransientModel):
    _name = 'regule.wizard'
    _description = "Wizard Regule"

    balance_id = fields.Many2one('account.daily.balance', string="Balance", required=True)

    reference_id = fields.Many2one(
        'account.daily.balance.line',
        string="Référence",
        required=True
    )

    montant = fields.Float(string="Montant", readonly=True, store=True)

    # ───────────────────────────────────────────────
    # Filtrer référence pour n'afficher que non régulés
    # ───────────────────────────────────────────────
    @api.onchange('balance_id')
    def _onchange_balance_id(self):
        if not self.balance_id:
            return {}

        # References déjà régulées
        reguled_refs = self.balance_id.line_ids.filtered(
            lambda l: l.libelle == 'REGULE'
        ).mapped('reference')

        return {
            'domain': {
                'reference_id': [
                    ('balance_id', '=', self.balance_id.id),
                    ('libelle', '!=', 'REGULE'),
                    ('reference', 'not in', reguled_refs)
                ]
            }
        }

    # Remplissage automatique du montant
    @api.onchange('reference_id')
    def _onchange_reference_id(self):
        if self.reference_id:
            self.montant = abs(self.reference_id.debit or self.reference_id.credit or 0)

    # ───────────────────────────────────────────────
    # CONFIRMATION REGULE
    # ───────────────────────────────────────────────
    from odoo import fields, _
    from odoo.exceptions import UserError

    def action_confirm_regule(self):
        self.ensure_one()

        # Interdire régulation de REGULE
        if self.reference_id.libelle == 'REGULE':
            raise UserError(_("Impossible de réguler une ligne REGULE."))

        # Interdire régule d'un jour passé
        today = fields.Date.context_today(self)
        if self.balance_id.date < today:
            raise UserError(_("Journal déjà clôturé, régulation impossible."))

        # Compter toutes les régules liées à cette référence
        regule_count = self.env['account.daily.balance.line'].search_count([
            ('balance_id', '=', self.balance_id.id),
            ('reference', '=', self.reference_id.reference),
            ('libelle', '=', 'REGULE')
        ])

        if regule_count >= 1:
            raise UserError(_("Cette référence a déjà été régulée, opération impossible."))

        montant = abs(self.reference_id.debit or self.reference_id.credit or 0)

        # Déterminer direction mouvement
        if self.reference_id.credit > 0:
            debit = montant
            credit = 0.0
        else:
            debit = 0.0
            credit = montant

        # Création ligne REGULE (une seule)
        self.env['account.daily.balance.line'].create({
            'balance_id': self.balance_id.id,
            'reference': self.reference_id.reference,
            'libelle': 'REGULE',
            'payment': self.reference_id.payment,
            'debit': debit,
            'credit': credit,
            'origin_line_id': self.reference_id.id,
        })

        # Annulation facture ou paiement ou dépense
        invoice = self.env['account.move'].search([('name', '=', self.reference_id.reference)], limit=1)

        if invoice and invoice.state not in ('cancel'):
            invoice.button_cancel()
        else:
            payment = self.env['account.payment'].search([('name', '=', self.reference_id.reference)], limit=1)
            if payment and payment.state != 'cancelled':
                payment.action_cancel()

            expense = self.env['hr.expense.sheet'].search([('name', '=', self.reference_id.reference)], limit=1)
            if expense and expense.payment_state != 'reversed':
                expense.write({'payment_state': 'reversed'})

        # Mise à jour totaux balance
        self.balance_id.action_update_totals()

        return {'type': 'ir.actions.act_window_close'}
