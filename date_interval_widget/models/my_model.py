from datetime import date, timedelta
from odoo import models, fields, api


class MyModel(models.Model):
    _name = "my.model"
    _description = "Planning des chambres sur intervalle"

    start_date = fields.Date(
        string="Date de début",
        required=True,
        default=lambda self: date.today()
    )
    end_date = fields.Date(
        string="Date de fin",
        required=True,
        default=lambda self: date.today() + timedelta(days=7)
    )
    day_list_html = fields.Html(
        string="Planning des chambres",
        compute="_compute_day_list_html",
        sanitize=False
    )

    @api.depends("start_date", "end_date")
    def _compute_day_list_html(self):
        for record in self:
            if not record.start_date or not record.end_date or record.end_date < record.start_date:
                record.day_list_html = ""
                continue

            # Générer la liste des jours de l'intervalle
            days = []
            current = record.start_date
            while current <= record.end_date:
                days.append(current)
                current += timedelta(days=1)

            # Récupérer toutes les chambres disponibles
            rooms = self.env["hotel.room"].search([], order="name")

            # Génération du tableau HTML
            html = """
            <div style="overflow-x: auto; border: 1px solid #ccc; border-radius: 8px; padding: 8px; max-width: 100%;">
                <table style="border-collapse: collapse; width: 100%; min-width: 900px; text-align: center;">
                    <thead>
                        <tr style="background: #f5f5f5;">
                            <th style="border: 1px solid #ddd; padding: 8px; background-color: #eee;">Chambre</th>
            """

            for day in days:
                html += f"<th style='border:1px solid #ddd; padding:8px; white-space:nowrap;'>{day.strftime('%d/%m/%Y')}</th>"

            html += "</tr></thead><tbody>"

            for room in rooms:
                html += f"<tr><td style='border:1px solid #ddd; padding:8px; font-weight:bold;'>{room.name}</td>"
                for _ in days:
                    html += "<td style='border:1px solid #ddd; padding:8px;'>—</td>"
                html += "</tr>"

            html += "</tbody></table></div>"

            record.day_list_html = html
