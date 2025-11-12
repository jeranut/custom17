{
    'name': 'Custom POS Screen',
    'version': '17.0.1.0.0',
    'summary': 'Add custom screen and payment button in POS',
    'depends': ['point_of_sale','hotel','hotel_reservation'],
    'assets': {
        'point_of_sale._assets_pos': [
            # 1️⃣ Charger ton écran avant le bouton
            'custom_pos_screen/static/src/app/screens/custom_screen.js',
            'custom_pos_screen/static/src/app/screens/custom_screen.xml',

            # 2️⃣ Charger ensuite le bouton du Payment Screen
            'custom_pos_screen/static/src/app/control_buttons/payment_button.js',
            'custom_pos_screen/static/src/app/control_buttons/payment_button.xml',
        ],

    },
    'data': [
        'views/partner_action.xml',
    ],
    'installable': True,
    'application': False,
}
