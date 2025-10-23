{
    "name": "POS Custom Button",
    "summary": "Ajoute un bouton d'impression dans la ProductScreen du POS (Odoo 17)",
    "version": "17.0.1.0.0",
    "author": "Toi",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "assets": {
        "point_of_sale._assets_pos": [
              # pour l'import printer
            "pos_custom_button/static/src/js/custom_button.js",
            "pos_custom_button/static/src/xml/custom_button.xml",
        ],
    },
    "installable": True,
    "application": False,
}
