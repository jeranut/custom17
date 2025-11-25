from odoo import models, api

class PosSession(models.Model):
    _inherit = "pos.session"

    def action_pos_session_close(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        res = super(PosSession, self).action_pos_session_close(
            balancing_account, amount_to_balance, bank_payment_method_diffs
        )

        # Récupérer les paiements
        payments = self.order_ids.payment_ids

        totals = {}
        for p in payments:
            journal_name = p.payment_method_id.name
            totals[journal_name] = totals.get(journal_name, 0) + p.amount

        for journal, amount in totals.items():
            if amount <= 0:
                continue

            reference = self.name
            libelle = "RECETTE RESTAURANT"

            # CASH ESPECES
            if journal.strip().lower() == "espèces restaurant":
                balance = self.env["account.daily.balance"].search(
                    [("date", "=", self.start_at.date())], limit=1
                )
                if not balance:
                    balance = self.env["account.daily.balance"].create({"date": self.start_at.date()})

                self.env["account.daily.balance.line"].create({
                    "balance_id": balance.id,
                    "reference": reference,
                    "libelle": libelle,
                    "payment": "cash",
                    "debit": 0.00,
                    "credit": amount,
                })
                balance.action_update_totals()

            # MOBILE MVOLA
            if journal.lower() in ["mvola", "mobile", "orange money", "airtel money"]:
                balance_mobile = self.env["account.daily.balance.mobile"].search(
                    [("date", "=", self.start_at.date())], limit=1
                )
                if not balance_mobile:
                    balance_mobile = self.env["account.daily.balance.mobile"].create({"date": self.start_at.date()})

                self.env["account.daily.balance.mobile.line"].create({
                    "balance_id": balance_mobile.id,
                    "reference": reference,
                    "libelle": libelle,
                    "payment": "mobile",
                    "debit": 0.0,
                    "credit": amount,
                    "regule_badge": "",
                })
                balance_mobile.action_update_totals_mobile()

        # RESET POS BALANCE à zéro
        self.cash_register_balance_start = 0.0
        self.cash_register_balance_end_real = 0.0

        return res
