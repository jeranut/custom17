from datetime import date, timedelta
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


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
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if not record.start_date or not record.end_date or record.end_date < record.start_date:
                record.day_list_html = ""
                continue

            # Générer la liste des jours
            days = []
            current = record.start_date
            while current <= record.end_date:
                days.append(current)
                current += timedelta(days=1)

            rooms = self.env["hotel.room"].search([], order="name")

            # Récupérer toutes les réservations sur la période
            reservation_lines = self.env["hotel.room.reservation.line"].search([
                ("check_in", "<=", record.end_date),
                ("check_out", ">=", record.start_date)
            ])

            # Indexation par chambre
            room_reservations = {}
            for line in reservation_lines:
                room_reservations.setdefault(line.room_id.id, []).append(line)

            # Légende en haut
            html = """
            <div style="margin-bottom:10px; font-size:13px;">
                <b>Légende :</b>
                <span style="background:#ffcc66; padding:4px 8px; margin-left:6px;">Confirmé</span>
                <span style="background:#99ccff; padding:4px 8px; margin-left:6px;">Check In</span>
                <span style="background:#99e699; padding:4px 8px; margin-left:6px;">Check Out</span>
            </div>
            <div style="overflow-x:auto; border:1px solid #ccc; border-radius:8px; padding:8px; max-width:100%;">
                <table style="border-collapse:collapse; width:100%; min-width:900px; text-align:center;">
                    <thead>
                        <tr style="background:#f5f5f5; position:sticky; top:0;">
                            <th style="border:1px solid #ddd; padding:8px; background-color:#eee;">Chambre</th>
            """

            # 🔹 Format de la date modifié ici
            for day in days:
                html += f"<th style='border:1px solid #ddd; padding:8px; white-space:nowrap;'>{day.strftime('%d-%b-%Y').upper()}</th>"

            html += "</tr></thead><tbody>"

            # Lignes du planning
            for room in rooms:
                html += f"<tr><td style='border:1px solid #ddd; padding:8px; font-weight:bold;'>{room.name}</td>"

                for day in days:
                    cell_color = "white"
                    cell_text = "&nbsp;"
                    tooltip = ""
                    cell_link = ""

                    for res_line in room_reservations.get(room.id, []):
                        check_in = res_line.check_in.date() if hasattr(res_line.check_in, "date") else res_line.check_in
                        check_out = res_line.check_out.date() if hasattr(res_line.check_out, "date") else res_line.check_out

                        if check_in <= day <= check_out:
                            res = res_line.reservation_id
                            if not res:
                                continue

                            # États réservation et folio
                            res_state = res.state or "N/A"
                            folio = res.folio_id
                            folio_state = folio.state if folio else False

                            # Couleur et texte selon les combinaisons
                            if res_state in ("draft", "brouillon"):
                                cell_color = "#d3d3d3"
                                cell_text = "Brouillon"
                            elif res_state in ("confirm", "confirmed"):
                                if not folio_state:
                                    cell_color = "#ffcc66"
                                    cell_text = "Confirmé"
                                elif folio_state == "draft":
                                    cell_color = "#99ccff"
                                    cell_text = "Check In"
                                elif folio_state in ("sale", "invoiced"):
                                    cell_color = "#99e699"
                                    cell_text = "Check Out"
                                else:
                                    cell_color = "#ffcc66"
                                    cell_text = "Confirmé"
                            elif res_state in ("done", "checkout"):
                                if folio_state == "draft":
                                    cell_color = "#99ccff"
                                    cell_text = "Check In"
                                elif folio_state in ("sale", "invoiced"):
                                    cell_color = "#99e699"
                                    cell_text = "Check Out"
                                else:
                                    cell_color = "#ffcc66"
                                    cell_text = "Confirmé"
                            elif res_state in ("cancel", "cancelled"):
                                cell_color = "#ff9999"
                                cell_text = "Annulé"

                            # Tooltip
                            partner_name = res.partner_id.name or "N/A"
                            res_name = getattr(res, "reservation_no", "") or getattr(res, "display_name", "") or "Réservation"
                            tooltip = (
                                f"Client : {partner_name}&#10;"
                                f"Réservation : {res_name}&#10;"
                                f"État réservation : {res_state.capitalize()}&#10;"
                                f"État folio : {(folio_state or 'Aucun folio').capitalize()}"
                            )

                            # Lien cliquable vers le folio
                            if folio:
                                cell_link = f"{base_url}/web#id={folio.id}&model=hotel.folio&view_type=form"
                            break

                    # Cellule HTML (avec lien si disponible)
                    if cell_link:
                        html += (
                            f"<td style='border:1px solid #ddd; padding:6px; background-color:{cell_color}; "
                            f"min-width:70px; cursor:pointer;' title=\"{tooltip}\">"
                            f"<a href='{cell_link}' target='_blank' "
                            f"style='color:black; text-decoration:none; display:block;'>{cell_text}</a></td>"
                        )
                    else:
                        html += (
                            f"<td style='border:1px solid #ddd; padding:6px; background-color:{cell_color}; "
                            f"min-width:70px;' title=\"{tooltip}\">{cell_text}</td>"
                        )

                html += "</tr>"

            html += "</tbody></table></div>"
            record.day_list_html = html
