# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class ProductProductInheritOD(models.Model):
    _inherit = 'product.product'

    material_type = fields.Many2one("material.type" , related='product_tmpl_id.material_type', store=True)
    conversion_value = fields.Float(string="Conversion Value",)
    conversion_uom_id = fields.Many2one("uom.uom", string="UOM",)
    converted_value = fields.Float(string="Converted Value", compute='_compute_converted_value')


    @api.depends('conversion_value', 'conversion_uom_id', 'converted_value', )
    def _compute_converted_value(self):
        for rec in self:
            stock_quant = rec.env['stock.quant'].search([('product_id', '=', rec.id), ], limit=1)
            if rec.conversion_value and stock_quant.quantity:
                rec.converted_value = stock_quant.quantity / rec.conversion_value
            else:
                rec.converted_value = 0
