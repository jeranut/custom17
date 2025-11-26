# -*- coding: utf-8 -*-
from odoo import models, fields, api

# ==========================================================
# Modèle stock.journal : Stockage des valeurs historiques
# ==========================================================
class StockJournal(models.Model):
    _name = 'stock.journal'
    _description = 'Stock History Journal (SI/SF)'

    stock_initial = fields.Float(string='Stock Initial (SI)', digits='Product Unit of Measure')
    stock_final = fields.Float(string='Stock Final (SF)', digits='Product Unit of Measure')

    move_line_id = fields.Many2one(
        'stock.move.line',
        string='Ligne de Mouvement',
        required=True,
        ondelete='cascade'
    )

    product_id = fields.Many2one('product.product', string='Produit', related='move_line_id.product_id', store=True)
    company_id = fields.Many2one('res.company', string='Société', related='move_line_id.company_id', store=True)

# ==========================================================
# Héritage stock.move.line
# ==========================================================
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    stock_journal_ids = fields.One2many('stock.journal', 'move_line_id', string='Historique SI / SF')
    show_move_columns = fields.Boolean(string="Afficher colonnes", default=True)
    stock_initial = fields.Float(
        string='Stock Initial (SI)',
        compute='_compute_journal_values',
        digits='Product Unit of Measure'
    )
    stock_final = fields.Float(
        string='Stock Final (SF)',
        compute='_compute_journal_values',
        digits='Product Unit of Measure'
    )

    # Champs pour l'affichage des filtres sélectionnés
    filter_product_name = fields.Char(
        string="Produit filtré",
        compute='_compute_filter_header',
        store=False
    )
    filter_date_from = fields.Char(
        string="Date depuis",
        compute='_compute_filter_header',
        store=False
    )
    filter_date_to = fields.Char(
        string="Date jusqu'à",
        compute='_compute_filter_header',
        store=False
    )

    @api.depends_context('filter_product_name', 'filter_date_from', 'filter_date_to')
    def _compute_filter_header(self):
        for line in self:
            line.filter_product_name = self.env.context.get('filter_product_name', '')
            line.filter_date_from = self.env.context.get('filter_date_from', '')
            line.filter_date_to = self.env.context.get('filter_date_to', '')

    @api.depends('stock_journal_ids')
    def _compute_journal_values(self):
        for line in self:
            journal = line.stock_journal_ids[:1]
            line.stock_initial = journal.stock_initial if journal else 0.0
            line.stock_final = journal.stock_final if journal else 0.0

    # ----------------------------------------------------------
    # SURCHARGE _action_done POUR ENREGISTRER SI & SF
    # ----------------------------------------------------------
    def _action_done(self):
        # Sauvegarde des SI AVANT action_done()
        journal_buffer = {}

        for line in self:
            if line.state not in ('done', 'cancel') and not line.stock_journal_ids:
                # Emplacement interne concerné par le SI
                location_for_si = line.location_id if line.location_id.usage == 'internal' else line.location_dest_id

                # Stock initial via stock.quant
                qty_initial = sum(self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', location_for_si.id),
                ]).mapped('quantity'))

                journal_buffer[line.id] = qty_initial

        # Exécute le super pour effectuer le mouvement
        result = super(StockMoveLine, self)._action_done()

        # Sauvegarde SF APRÈS action_done
        for line in self:
            if line.id in journal_buffer and not line.stock_journal_ids:

                # Emplacement interne impacté pour le SF
                location_for_sf = (
                    line.location_dest_id if line.location_dest_id.usage == 'internal'
                    else line.location_id if line.location_id.usage == 'internal'
                    else False
                )

                if location_for_sf:
                    qty_final = sum(self.env['stock.quant'].search([
                        ('product_id', '=', line.product_id.id),
                        ('location_id', '=', location_for_sf.id),
                    ]).mapped('quantity'))
                else:
                    qty_final = 0.0

                # Création de l'entrée journal
                self.env['stock.journal'].create({
                    'move_line_id': line.id,
                    'stock_initial': journal_buffer[line.id],
                    'stock_final': qty_final,
                })

        return result


# ==========================================================
# Wizard pour filtrer les mouvements
# ==========================================================
class StockMoveLineFilterWizard(models.TransientModel):
    _name = 'stock.move.line.filter.wizard'
    _description = 'Filtrer les mouvements de stock'

    product_id = fields.Many2one('product.product', string='Produit')
    date_from = fields.Date(string='Date depuis')
    date_to = fields.Date(string='Date jusqu\'à')

    def apply_filter(self):
        domain = []
        context = dict(self.env.context)

        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
            context['filter_product_name'] = self.product_id.display_name
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
            context['filter_date_from'] = str(self.date_from)
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
            context['filter_date_to'] = str(self.date_to)

        # Récupère l'action et injecte domain + contexte
        action = self.env.ref('stock_move_line_extra.action_stock_move_line_history').read()[0]
        action['domain'] = domain
        action['context'] = context
        return action
