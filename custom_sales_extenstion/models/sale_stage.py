from odoo import api, fields, models, tools

from email.policy import default


class SaleStage(models.Model):
    _name = "sale.stage"


    code = fields.Char(string='Stage Code', required=True, copy=False, default=lambda self: self._generate_sequence_code())
    name = fields.Char(string='Stage name', required=True)
    stageusers = fields.Many2many('res.users', string='Related users')
    sale_template = fields.Many2one('sale.stage.type', string='Sale template', required=False)
    stageorder = fields.Integer(string='Stage Rank',default=0, required=True)
    _sql_constraints = [
        ('stage_code_unique', 'unique(code)', 'stage code already exists!')
    ]
    issystem = fields.Boolean(string='internal', default=False, invisible=True)
    approvetype = fields.Selection([('sequence', 'sequence')], string='Approve Mode',
                                   default='sequence')

    @api.model
    def _generate_sequence_code(self):
        """Generate an auto-incremented code using the sequence"""
        self.env.cr.execute("SELECT nextval('seq_stage_users')")
        seq_value = self.env.cr.fetchone()[0]
        return f"STAGE-{seq_value}"


    @api.depends('sale_template')
    def _compute_stage_code(self):
        for stage in self:
            stage.new_code = self._generate_sequence_code()
