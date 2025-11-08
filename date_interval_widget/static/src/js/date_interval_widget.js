/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillUpdateProps } from "@odoo/owl";

export class DateIntervalWidget extends Component {
    setup() {
        this.state = useState({ days: [] });
        this.computeDays();
        onWillUpdateProps(() => this.computeDays());
    }

    computeDays() {
        const { date_start, date_end } = this.props.record.data;
        if (date_start && date_end) {
            const start = new Date(date_start);
            const end = new Date(date_end);
            const days = [];
            for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
                days.push(new Date(d));
            }
            this.state.days = days;
        } else {
            this.state.days = [];
        }
    }
}

DateIntervalWidget.template = "date_interval_widget.DateIntervalWidgetTemplate";
registry.category("fields").add("date_interval_table", DateIntervalWidget);
