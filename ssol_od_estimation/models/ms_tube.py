from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError
import math


class MsTube(models.Model):
    _name = "ms.tube"
    _description = "ms Tube"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "parent_order_id"

    parent_order_id = fields.Many2one('order.estimation', string='Parent Order', tracking=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True, related='parent_order_id.partner_id')
    total_amount = fields.Float(string="Total Amount", tracking=True, compute='_compute_total_amount')
    order_date = fields.Date("Date", tracking=True, default=date.today())
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self:self.env.user.id, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self:self.env.company.id, readonly=True)
    attachment = fields.Binary(string="Attachment", tracking=True)
    description = fields.Text(string="Note", tracking=True)

    active = fields.Boolean(string="Active", default=True)
    image_1920 = fields.Binary(string='Image')

    ms_tube_line = fields.One2many("ms.tube.line", "order_id", string="")

    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')
    ], string="State", default='draft')

    def action_draft(self):
        self.state = "draft"

    def action_confirmed(self):
        self.state = "confirmed"

    def action_cancel(self):
        self.state = "cancel"


    @api.depends('total_amount', 'ms_tube_line', 'ms_tube_line.price_total')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.ms_tube_line:
                total_amount += line.price_total

            rec.total_amount = total_amount

    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('Only cancelled record. You can Delete!'))
            if not rec.env.user.has_group('ssol_od_estimation.group_order_estimation_delete_access'):
                raise UserError(_('You can not delete this Maintenance Record. Contact your administrator.'))
            else:
                return super(MsTube, self).unlink()





class MsTubeLine(models.Model):
    _name = 'ms.tube.line'


    order_id = fields.Many2one('ms.tube', string='Order Reference', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='order_id.company_id', store=True, index=True)
    product_id = fields.Many2one(comodel_name='product.product', check_company=True, domain=lambda self: self._product_id_domain())
    sr_no = fields.Integer(string="Sr No.", compute='_compute_sr_no', store=True)
    sr_no_char = fields.Char(string="Sr No.", compute='_compute_sr_no', store=True)
    name = fields.Text(string="Description", compute='_compute_name',  store=True)

    product_uom_id = fields.Many2one(comodel_name='uom.uom', string="Unit of Measure", compute='_compute_product_uom_id',
        store=True, readonly=False, precompute=True,
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_uom_qty = fields.Float(string='Qty', store=True, default=1)

    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self._default_currency_id())
    # price_unit = fields.Monetary(string="Price W/Kg")
    price_unit = fields.Monetary(string="Price / Kg")
    price_subtotal = fields.Monetary(string="Subtotal", compute='_compute_price_subtotal')
    cost_price = fields.Monetary(string='Cost', currency_field='currency_id', compute='_compute_cost_margin')
    profit_margin = fields.Monetary(string='Margin', currency_field='currency_id', compute='_compute_cost_margin')
    tax_id = fields.Many2many('account.tax', string="Taxes", store=True, context={'active_test': False}, check_company=True)
    discount = fields.Monetary(string="Discount")
    disc_percentage = fields.Monetary(string="Disc%")
    amount_taxed = fields.Monetary(string="Tax Excl.", compute='_compute_amount_taxed')
    price_total = fields.Monetary(string="Tax Incl.", compute='_compute_amount_total')



    tube_inches = fields.Selection(string="Inches",
                                     selection=[('½"', '½"'),
                                                ('3/8"', '3/8"'),('3/4”', '3/4”'),
                                                ('1"', '1"'),('1 ¼"', '1 ¼"'),
                                                ('1 ½"', '1 ½"'),('1 ¾"', '1 ¾"'),
                                                ('2"', '2"'),('2 ¼"', '2 ¼"'),
                                                ('2"', '2"'),('2 ¼"', '2 ¼"'),
                                                ('2 ½"', '2 ½"'),('2 ¾"', '2 ¾"'),
                                                ('3"', '3"')
                                                ], default='3/8"')
    tube_mm = fields.Float(string="MM", compute='_compute_tube_mm_thickness')

    thickness = fields.Float(string="W.T", compute='_compute_tube_mm_thickness')


    ms_weight = fields.Float(string="Weight of one Coil", compute='_compute_tube_mm_thickness')
    length_inches = fields.Float(string="Length(Inches)")
    total_ms = fields.Float(string="No. of Tube from one Coil", compute='_compute_total_ms')
    total_coil_required = fields.Float(string="No. of Coil Required", compute='_compute_total_coil_required')
    total_weight = fields.Float(string="Total Weight", digits=(16, 2), compute='_compute_total_weight')


    @api.depends('tube_inches', 'tube_mm', 'thickness', 'ms_weight', 'product_id')
    def _compute_tube_mm_thickness(self):
        for line in self:
            if line.tube_inches == '½"':
                line.tube_mm = 12.7
                line.thickness = 2.00
                line.ms_weight = 3.2

            elif line.tube_inches == '3/8"':
                line.tube_mm = 17.0
                line.thickness = 2.50
                line.ms_weight = 5.5

            elif line.tube_inches == '3/4”':
                line.tube_mm = 19.0
                line.thickness = 2.30
                line.ms_weight = 5.8

            elif line.tube_inches == '1"':
                line.tube_mm = 25.4
                line.thickness = 2.60
                line.ms_weight = 8.9

            elif line.tube_inches == '1 ¼"':
                line.tube_mm = 31.8
                line.thickness = 3.25
                line.ms_weight = 14

            elif line.tube_inches == '1 ½"':
                line.tube_mm = 38.1
                line.thickness = 3.25
                line.ms_weight = 17

            elif line.tube_inches == '1 ¾"':
                line.tube_mm = 44.5
                line.thickness = 3.25
                line.ms_weight = 20

            elif line.tube_inches == '2"':
                line.tube_mm = 50.8
                line.thickness = 3.25
                line.ms_weight = 23

            elif line.tube_inches == '2 ¼"':
                line.tube_mm = 57.0
                line.thickness = 3.25
                line.ms_weight = 26

            elif line.tube_inches == '2 ½"':
                line.tube_mm = 63.5
                line.thickness = 3.25
                line.ms_weight = 30

            elif line.tube_inches == '2 ¾"':
                line.tube_mm = 70.0
                line.thickness = 3.25
                line.ms_weight = 33

            elif line.tube_inches == '3"':
                line.tube_mm = 76.1
                line.thickness = 3.65
                line.ms_weight = 40

            else:
                line.tube_mm = False
                line.thickness = False
                line.ms_weight = False



    @api.depends('total_ms', 'length_inches', 'product_id')
    def _compute_total_ms(self):
        for line in self:
            if line.length_inches:
                line.total_ms = 600/line.length_inches
            else:
                line.total_ms = False



    @api.depends('total_ms', 'length_inches', 'product_uom_qty', 'product_id')
    def _compute_total_coil_required(self):
        for line in self:
            if line.total_ms:
                total_coil = line.product_uom_qty / line.total_ms
                # Round up to the next integer if there is a fractional part
                line.total_coil_required = math.ceil(total_coil)
            else:
                line.total_coil_required = False


    @api.depends('total_weight', 'ms_weight', 'product_uom_qty','total_coil_required', 'product_id')
    def _compute_total_weight(self):
        for line in self:
            if line.total_coil_required:
                line.total_weight = line.total_coil_required * line.ms_weight
            else:
                line.total_weight = False



    # === COMPUTE METHODS ===#
    @api.depends('product_id')
    def _compute_name(self):
        for option in self:
            if not option.product_id:
                continue
            option.name = option.product_id.get_product_multiline_description_sale()

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for option in self:
            option.product_uom_id = option.product_id.uom_id

    @api.model
    def _product_id_domain(self):
        """ Returns the domain of the products that can be added to the template. """
        return [('sale_ok', '=', True)]


    def _default_currency_id(self):
        return self.env.user.company_id.currency_id



    @api.depends('profit_margin', 'cost_price', 'product_id', 'total_weight', 'price_unit')
    def _compute_cost_margin(self):
        for line in self:
            if line.product_id:
                cost_subtotal = line.product_id.standard_price * line.total_weight
                line.cost_price = cost_subtotal
                unit_price_subtotal = line.price_unit * line.total_weight
                line.profit_margin = (unit_price_subtotal - cost_subtotal)
            else:
                line.cost_price = False
                line.profit_margin = False


    # === CUSTOM COMPUTE METHODS ===#
    @api.depends('order_id.ms_tube_line', 'sr_no', 'sr_no_char')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            value_sr = 1
            for line in order.ms_tube_line:
                value_sr += 1

    @api.depends('product_id', 'price_unit', 'price_subtotal', 'total_weight')
    def _compute_price_subtotal(self):
        for line in self:
            subtotal = line.price_unit * line.total_weight
            line.price_subtotal = subtotal

    @api.depends('product_id', 'price_unit', 'price_subtotal', 'total_weight', 'amount_taxed', 'tax_id')
    def _compute_amount_taxed(self):
        for rec in self:
            percentage_total = 0
            for line in rec.tax_id:
                percentage_total += line.amount
            taxed_amount = (rec.price_subtotal /100) * percentage_total
            rec.amount_taxed = rec.price_subtotal + taxed_amount

    @api.depends('product_id', 'price_unit', 'price_subtotal', 'total_weight', 'amount_taxed', 'tax_id', 'price_total', 'discount', 'disc_percentage')
    def _compute_amount_total(self):
        for line in self:
            disc_percentage = (line.amount_taxed / 100) * line.disc_percentage
            line.price_total =  line.amount_taxed - (line.discount + disc_percentage)



class CopperTubeLine(models.Model):
    _name = 'copper.tube.line'