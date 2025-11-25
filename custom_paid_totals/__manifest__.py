{
    'name': 'TRESORERIE',
    'version': '17.0.1.0.0',
    'summary': 'Rapport journalier des totaux débit/crédit',
    'category': 'Accounting',
    'author': 'Sysadptpro',
    'depends': ['account', 'hr_expense', 'web', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/paid_totals_views.xml',
        'views/paid_totals_views_mobile.xml',
        'views/journal_libel.xml',
        'views/invoice_date_read_only.xml',

    ],

    'installable': True,
    'application': True,
}
