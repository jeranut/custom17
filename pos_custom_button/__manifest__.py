{
    'name': 'POS Custom Button (OWL2 Patch)',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Add a custom button in the POS Payment Screen',
    'depends': ['point_of_sale'],
    'assets': {
        # 👉 Odoo 17 POS assets bundle
        'point_of_sale._assets_pos': [
            'pos_custom_buttons/static/src/js/payment_button.js',
        ],

        # 👉 OWL templates go here
        'web.asset_qweb': [
            'pos_custom_buttons/static/src/xml/payment_button.xml',
        ],
    },
    'installable': True,
    'application': False,
}
