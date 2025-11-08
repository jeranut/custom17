from odoo import models, fields, api
from datetime import timedelta

class MyModel(models.Model):
    _name = "my.model"
    _description = "Intervalle de Dates"

    name = fields.Char(string="Nom", required=True)
    start_date = fields.Date(string="Date de début", required=True)
    end_date = fields.Date(string="Date de fin", required=True)
    day_count = fields.Integer(string="Nombre de jours", compute="_compute_day_count", store=True)

    # Contenu HTML du tableau des jours
    day_list_html = fields.Html(string="Liste des jours", compute="_compute_day_list", sanitize=False)

    @api.depends("start_date", "end_date")
    def _compute_day_count(self):
        for record in self:
            if record.start_date and record.end_date:
                record.day_count = (record.end_date - record.start_date).days + 1
            else:
                record.day_count = 0

    @api.depends("start_date", "end_date")
    def _compute_day_list(self):
        for record in self:
            if record.start_date and record.end_date and record.end_date >= record.start_date:
                days = (record.end_date - record.start_date).days + 1
                # 💡 Style tableau avec barre de défilement horizontale
                html = """
                <div style='overflow-x: auto; border: 1px solid #ccc; border-radius: 6px; padding: 5px;'>
                    <table style='border-collapse: collapse; min-width: max-content;'>
                        <tr>
                """
                for i in range(days):
                    day = record.start_date + timedelta(days=i)
                    html += f"""
                        <th style='border: 1px solid #ccc; padding: 8px 12px; background-color: #f0f0f0; white-space: nowrap;'>
                            {day.strftime('%d/%m/%Y')}
                        </th>
                    """
                html += """
                        </tr>
                    </table>
                </div>
                """
                record.day_list_html = html
            else:
                record.day_list_html = ""
