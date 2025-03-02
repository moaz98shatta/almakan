from odoo import api, fields, models, tools


class SaleStage(models.Model):
    _name = "sale.stage"
    code = fields.Char(string='Stage code', required=True)
    name = fields.Char(string='Stage name', required=True)
    stageusers = fields.Many2many('res.users', string='Related users')
    sale_template = fields.Many2one('sale.stage.type', string='Sale template', required=False)
    stageorder = fields.Integer(string='Stage Rank', required=True)
    _sql_constraints = [
        ('stage_code_unique', 'unique(code)', 'stage code already exists!')
    ]
    issystem = fields.Boolean(string='internal', default=False, invisible=True)
    approvetype = fields.Selection([('sequence', 'sequence')], string='Approve Mode',
                                   default='sequence')
