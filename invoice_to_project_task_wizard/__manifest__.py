{
    "name": "Invoice → Project Task (Wizard selector)",
    "version": "17.0.1.1.0",
    "summary": "Wizard de sélection de projet depuis Facturation (fix: sans field task_created)",
    "category": "Accounting/Project",
    "license": "LGPL-3",
    "author": "SystAdaptpro",
    "depends": ["account", "project"],
    "data": [
        "security/ir.model.access.csv",
        "views/task_wizard_view.xml",
        "views/account_move_button_wizard.xml"
    ],
    "installable": True,
    "application": False
}
