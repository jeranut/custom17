{
    'name': 'print session',
    'version': '1.0',
    'summary': 'Send POS receipts to Flask printer server',
    'category': 'Point of Sale',
    'author': 'Your Name',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_session_views.xml',
    ],

    'installable': True,
    'application': True,
}