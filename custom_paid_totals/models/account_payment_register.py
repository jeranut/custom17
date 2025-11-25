from odoo import models, api, fields, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):
        journal = self.journal_id
        journal_type = journal.type if journal else "N/A"

        warning_message = _(
            "⚠ Vous allez effectuer un paiement en utilisant le journal :\n\n"
            f"🧾 Nom du journal  : {journal.name}\n"
            f"🏦 Type du journal : {journal_type.upper()}\n\n"
            "Confirmez-vous cette opération ?"
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'popup.warning.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_message': warning_message,
                'payment_register_id': self.id,
            },
        }


class PopupWarningMessage(models.TransientModel):
    _name = 'popup.warning.message'
    _description = 'Message Popup'

    message = fields.Text(string="Message", readonly=True)

    def action_confirm(self):
        payment_register = self.env['account.payment.register'].browse(
            self.env.context.get('payment_register_id')
        )
        return payment_register._create_payments()
