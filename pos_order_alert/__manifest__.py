# -*- coding: utf-8 -*-
{
    "name": "POS Order Alert",
    "summary": "Affiche une alerte quand on clique sur Order dans le POS",
    "version": "17.0.1.0.0",
    "author": "SystAdaptpro",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "pos_restaurant"],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_order_alert/static/src/js/order_alert.js"
        ]
    },
    "installable": True,
    "application": False
}
