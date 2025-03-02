from odoo import api, fields, models, tools


class SaleStageType(models.Model):
    _name = "sale.stage.type"
    name = fields.Char(string='Sale template', required=True)
    stages = fields.One2many('sale.stage', 'sale_template', string='stages')
    pricelist = fields.Many2one('product.pricelist', string='PriceList', required=False)

    def get_stage_list(self):
        lst = []
        for rec in self.stages:
            lst.append(rec.code)
        return lst
