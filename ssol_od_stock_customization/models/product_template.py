# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class ProductTemplateInheritOD(models.Model):
    _inherit = 'product.template'

    material_type = fields.Many2one("material.type", string="Material Type")
    conversion_value = fields.Float(string="Conversion Value", )
    conversion_uom_id = fields.Many2one("uom.uom", string="UOM")
    converted_value = fields.Float(string="Converted Value", compute='_compute_converted_value')

    @api.depends('conversion_value', 'conversion_uom_id', 'converted_value')
    def _compute_converted_value(self):
        for rec in self:

            stock_quant = rec.env['stock.quant'].search([('product_tmpl_id', '=', rec.id), ], limit=1)
            if rec.conversion_value and stock_quant.quantity:
                rec.converted_value = stock_quant.quantity / rec.conversion_value
            else:
                rec.converted_value = 0


    """SEQUENCE GENERATE ON INTERNAL REFERENCE"""
    @api.model
    def create(self, values):
        values['default_code'] = self.env['ir.sequence'].next_by_code('product.template') or _('New')
        res = super(ProductTemplateInheritOD, self).create(values)
        return res


