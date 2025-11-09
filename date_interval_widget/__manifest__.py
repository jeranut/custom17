{
    'name': 'Date Interval Widget',
    'version': '17.0.1.0.0',
    'depends': ['base', 'web'],
    'data': [
        'security/security.xml',
        'views/my_model_view.xml',       # L’action est ici -> doit venir avant
        'security/ir.model.access.csv',  # CSV à la fin
    ],
    'assets': {
        'web.assets_backend': [
            'date_interval_widget/static/src/js/date_interval_widget.js',
            'date_interval_widget/static/src/xml/date_interval_widget.xml',
        ],
    },
    'installable': True,
    'application': True,
}
