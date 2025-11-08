/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class RoomReservationWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            summary_header: [],
            room_summary: [],   // Toujours initialisé
        });

        onWillStart(async () => {
            await this.loadSummary();
        });
    }

    async loadSummary() {
        try {
            const result = await this.orm.call("hotel.room", "get_room_summary", []);
            this.state.summary_header = result.summary_header || [];
            this.state.room_summary = result.room_summary || [];
        } catch (error) {
            console.error("Erreur chargement résumé chambres :", error);
        }
    }

    async load_form(room_id, date, ev) {
        if (!room_id) return;
        const actionService = useService("action");
        await actionService.doAction({
            type: "ir.actions.act_window",
            name: "Room Reservation",
            res_model: "hotel.reservation",
            views: [[false, "form"]],
            target: "current",
            context: {
                default_room_id: room_id,
                default_checkin: date,
            },
        });
    }
}

RoomReservationWidget.template = "RoomSummary";

// Enregistrement comme widget de champ
registry.category("fields").add("Room_Reservation", RoomReservationWidget);
