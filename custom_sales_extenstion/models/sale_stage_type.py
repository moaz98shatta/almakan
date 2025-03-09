from odoo import api, fields, models, tools


class SaleStageType(models.Model):
    _name = "sale.stage.type"
    name = fields.Char(string='Sale template', required=True)
    stages = fields.One2many('sale.stage', 'sale_template', string='Stages')
    pricelist = fields.Many2one('product.pricelist', string='PriceList', required=False)

    def get_stage_list(self):
        lst = []
        for rec in self.stages:
            lst.append(rec.code)
        return lst



    # @api.depends("pricelist")  # Triggers recomputation when a SaleStageType is updated
    # def _compute_stages(self):
    #     for record in self:
    #         if not record.stages:  # Only populate if empty
    #             stage_list = []
    #             stage_list.append((0, 0, {
    #                 "code": self.env["ir.sequence"].next_by_code("sale.stage.code") or "00000",
    #             }))
    #
    #             record.update({"stages": stage_list})  #


    def unlink(self):
        """Ensure stages are deleted when SaleStageType is deleted."""
        for record in self:
            stages = self.env['sale.stage'].search([('sale_template', '=', record.id)])
            stages.unlink()  # Delete related SaleStage records
        return super(SaleStageType, self).unlink()
