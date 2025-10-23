{
    "name": "POS Payment Alert",
    "version": "17.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Afficher une alerte lors de la validation du paiement POS",
    "author": "SystAdaptpro",
    "website": "https://systadaptpro.com",
    "depends": ["point_of_sale"],
    "data": [],
    "assets": {
        "point_of_sale.assets": [
            "pos_payment_alert/static/src/js/payment_alert.js",
        ],
    },
    "installable": True,
    "application": False
}