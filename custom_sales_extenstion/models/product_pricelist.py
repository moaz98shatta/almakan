# -*- coding: utf-8 -*-

from odoo import _, api, models ,fields

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    min_price = fields.Float(string="Min Price")

