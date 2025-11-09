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

            # Liste des jours
            days = []
            current = record.start_date
            while current <= record.end_date:
                days.append(current)
                current += timedelta(days=1)

            rooms = self.env["hotel.room"].search([], order="name")

            # Récupération des réservations confirmées ou en cours
            reservation_lines = self.env["hotel.room.reservation.line"].search([
                ("check_in", "<=", record.end_date),
                ("check_out", ">=", record.start_date)
            ])

            # Indexation des réservations par chambre
            room_reservations = {}
            for res_line in reservation_lines:
                room_reservations.setdefault(res_line.room_id.id, []).append(res_line)

            # Construction du tableau
            html = """
            <div style="overflow-x: auto; border: 1px solid #ccc; border-radius: 8px; padding: 8px; max-width: 100%;">
                <table style="border-collapse: collapse; width: 100%; min-width: 900px; text-align: center;">
                    <thead>
                        <tr style="background: #f5f5f5; position: sticky; top: 0;">
                            <th style="border: 1px solid #ddd; padding: 8px; background-color: #eee;">Chambre</th>
            """

            for day in days:
                html += f"<th style='border:1px solid #ddd; padding:8px; white-space:nowrap;'>{day.strftime('%d/%m')}</th>"

            html += "</tr></thead><tbody>"

            # Remplir le tableau par chambre
            for room in rooms:
                html += f"<tr><td style='border:1px solid #ddd; padding:8px; font-weight:bold;'>{room.name}</td>"

                for day in days:
                    cell_color = "white"
                    cell_text = "&nbsp;"

                    # Vérifie si une réservation couvre ce jour
                    for res_line in room_reservations.get(room.id, []):
                        check_in = fields.Date.to_date(res_line.check_in)
                        check_out = fields.Date.to_date(res_line.check_out)
                        if check_in <= day <= check_out:
                            state = res_line.reservation_id.state
                            if state == "draft":
                                cell_color = "#d3d3d3"  # gris
                            elif state == "confirm":
                                cell_color = "#ffcc66"  # orange
                            elif state == "in":
                                cell_color = "#66b3ff"  # bleu (client présent)
                            elif state == "done":
                                cell_color = "#99e699"  # vert
                            elif state == "cancel":
                                cell_color = "#ff9999"  # rouge
                            cell_text = state.capitalize()
                            break

                    html += f"<td style='border:1px solid #ddd; padding:6px; background-color:{cell_color}; min-width:70px;'>{cell_text}</td>"

                html += "</tr>"

            html += "</tbody></table></div>"

            # Légende des couleurs
            html += """
            <div style="margin-top:8px; font-size:13px;">
                <b>Légende :</b>
                <span style="background:#d3d3d3; padding:4px 8px; margin-left:6px;">Brouillon</span>
                <span style="background:#ffcc66; padding:4px 8px; margin-left:6px;">Confirmé</span>
                <span style="background:#66b3ff; padding:4px 8px; margin-left:6px;">IN (Client présent)</span>
                <span style="background:#99e699; padding:4px 8px; margin-left:6px;">Terminé</span>
                <span style="background:#ff9999; padding:4px 8px; margin-left:6px;">Annulé</span>
            </div>
            """

            record.day_list_html = html
