from odoo import api, fields, models, tools


class SaleOrderAccept(models.Model):
    _name = "sale.order.pending"
    user = fields.Many2one('res.users', string='user')
    saleorder = fields.Many2one('sale.order', string='sale order')
    state = fields.Char(string='stage')
    status = fields.Selection(selection=[
        ('approve', 'Approve'),
        ('decline', 'Decline'),
        ('queue', 'Queue'),
        ('waiting', 'Waiting'),
    ], default='waiting')
    userorder = fields.Integer(string='user order', default=0)
