{
    'name': 'TRESORERIE',
    'version': '17.0.1.0.0',
    'summary': 'Rapport journalier des totaux débit/crédit',
    'category': 'Accounting',
    'author': 'Sysadptpro',
    'depends': ['account', 'hr_expense', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/paid_totals_views.xml',
        'views/journal_libel.xml',
        'views/invoice_date_read_only.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/custom_paid_totals/static/src/js/paid_totals_date_filter.js',
        ],
    },
    'installable': True,
    'application': True,
}
