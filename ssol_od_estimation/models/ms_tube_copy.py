from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError
from collections import defaultdict
import math


class MsTube(models.Model):
    _name = "ms.tube"
    _description = "Ms Tube"
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


    order_id = fields.Many2one('ms.tube', string='Estimation Order Reference', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='order_id.company_id', store=True, index=True)
    product_id = fields.Many2one(comodel_name='product.product', check_company=True, domain=lambda self: self._product_id_domain())
    sr_no = fields.Integer(string="Sr No.", compute='_compute_sr_no', store=True)
    sr_no_char = fields.Char(string="Sr No.", compute='_compute_sr_no', store=True)
    name = fields.Text(string="Description", compute='_compute_name',  store=True)

    product_uom_id = fields.Many2one(comodel_name='uom.uom', string="Unit of Measure", compute='_compute_product_uom_id',
        store=True, readonly=False, precompute=True,
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')


    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self._default_currency_id())
    price_unit = fields.Float(string="Total Rft")
    price_subtotal = fields.Monetary(string="Subtotal", compute='_compute_price_subtotal')
    cost_price = fields.Monetary(string='Cost', currency_field='currency_id', compute='_compute_cost_margin')
    profit_margin = fields.Monetary(string='Margin', currency_field='currency_id', compute='_compute_cost_margin')
    tax_id = fields.Many2many('account.tax', string="Taxes", store=True, context={'active_test': False}, check_company=True)
    discount = fields.Monetary(string="Discount")
    disc_percentage = fields.Monetary(string="Disc%")
    amount_taxed = fields.Monetary(string="Tax Excl.", compute='_compute_amount_taxed')
    price_total = fields.Monetary(string="Tax Incl.", compute='_compute_amount_total')


    ms_tube_size = fields.Selection(string="NB/MM (Inches)",
                                     selection=[('12.7(½")','12.7 mm__________(½")'),
                                                ('17.0(3/8")','17.0 mm__________(3/8")'),
                                                ('19.0(3/4”)','19.0 mm__________(3/4”)'),
                                                ('25.4(1")','25.4 mm__________(1")'),
                                                ('31.8(1 ¼")','31.8 mm__________(1 ¼")'),
                                                ('38.1(1 ½")','38.1 mm__________(1 ½")'),
                                                ('44.5(1 ¾")','44.5 mm__________(1 ¾")'),
                                                ('50.8(2")','50.8 mm__________(2")'),
                                                ('57.0(2 ¼")','57.0 mm__________(2 ¼")'),
                                                ('63.5(2 ½")','63.5 mm__________(2 ½")'),
                                                ('70.0(2 ¾")','70.0 mm__________(2 ¾")'),
                                                ('76.1(3")','76.1 mm__________(3")'),

                                                ], default='50.8(2")')

    ms_tube_medium = fields.Float(string="Tube Weight (kg)", compute='_compute_ms_tube_medium')

    thickness = fields.Float(string="Th.", compute='_compute_thickness')
    rate_per_rft = fields.Float(string="Rate / Rft")
    product_uom_qty = fields.Float(string='Qty', compute='_compute_product_uom_qty')
    total_weight = fields.Float(string="Total Weight (Kg)", digits=(16, 2), compute='_compute_total_weight')

    @api.depends('total_weight', 'ms_tube_medium', 'product_uom_qty', 'product_id')
    def _compute_total_weight(self):
        for line in self:
            if line.product_uom_qty:
                line.total_weight = line.ms_tube_medium * line.product_uom_qty
            else:
                line.total_weight = False

    @api.depends('ms_tube_size', 'ms_tube_medium')
    def _compute_ms_tube_medium(self):
        for line in self:

            if line.ms_tube_size == '12.7(½")':
                line.ms_tube_medium = '3.2'

            elif line.ms_tube_size == '17.0(3/8")':
                line.ms_tube_medium = '5.5'

            elif line.ms_tube_size == '19.0(3/4”)':
                line.ms_tube_medium = '5.8'

            elif line.ms_tube_size == '25.4(1")':
                line.ms_tube_medium = '8.9'

            elif line.ms_tube_size == '31.8(1 ¼")':
                line.ms_tube_medium = '14'

            elif line.ms_tube_size == '38.1(1 ½")':
                line.ms_tube_medium = '17'

            elif line.ms_tube_size == '44.5(1 ¾")':
                line.ms_tube_medium = '20'

            elif line.ms_tube_size == '50.8(2")':
                line.ms_tube_medium = '23'

            elif line.ms_tube_size == '57.0(2 ¼")':
                line.ms_tube_medium = '26'

            elif line.ms_tube_size == '63.5(2 ½")':
                line.ms_tube_medium = '30'

            elif line.ms_tube_size == '70.0(2 ¾")':
                line.ms_tube_medium = '33'

            elif line.ms_tube_size == '76.1(3")':
                line.ms_tube_medium = '40'

            else:
                line.ms_tube_medium = False


    @api.depends('ms_tube_size')
    def _compute_thickness(self):
        for line in self:

            if line.ms_tube_size == '12.7(½")':
                    line.thickness = 2.00

            elif line.ms_tube_size == '17.0(3/8")':
                    line.thickness = 2.50


            elif line.ms_tube_size == '19.0(3/4”)':
                    line.thickness = 2.30

            elif line.ms_tube_size == '25.4(1")':
                    line.thickness = 2.60

            elif line.ms_tube_size == '31.8(1 ¼")':
                    line.thickness = 3.25

            elif line.ms_tube_size == '38.1(1 ½")':
                    line.thickness = 3.25

            elif line.ms_tube_size == '44.5(1 ¾")':
                    line.thickness = 3.25

            elif line.ms_tube_size == '50.8(2")':
                    line.thickness = 3.25

            elif line.ms_tube_size == '57.0(2 ¼")':
                    line.thickness = 3.25

            elif line.ms_tube_size == '63.5(2 ½")':
                    line.thickness = 3.25

            elif line.ms_tube_size == '70.0(2 ¾")':
                    line.thickness = 3.25

            elif line.ms_tube_size == '76.1(3")':
                    line.thickness = 3.65

            else:
                line.thickness = False

    @api.depends('product_uom_qty', 'price_unit', 'ms_tube_size', 'ms_tube_medium', 'product_id')
    def _compute_product_uom_qty(self):
        for line in self:
            line.product_uom_qty = math.ceil(line.price_unit/20)

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



    @api.depends('profit_margin', 'cost_price', 'product_id', 'rate_per_rft', 'price_unit')
    def _compute_cost_margin(self):
        for line in self:
            if line.product_id:
                cost_subtotal = line.product_id.standard_price * line.rate_per_rft
                line.cost_price = cost_subtotal
                unit_price_subtotal = line.price_unit * line.rate_per_rft
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

    @api.depends('product_id', 'price_unit', 'price_subtotal', 'rate_per_rft')
    def _compute_price_subtotal(self):
        for line in self:
            subtotal = line.price_unit * line.rate_per_rft
            line.price_subtotal = subtotal

    @api.depends('product_id', 'price_unit', 'price_subtotal', 'rate_per_rft', 'amount_taxed', 'tax_id')
    def _compute_amount_taxed(self):
        for rec in self:
            percentage_total = 0
            for line in rec.tax_id:
                percentage_total += line.amount
            taxed_amount = (rec.price_subtotal /100) * percentage_total
            rec.amount_taxed = rec.price_subtotal + taxed_amount

    @api.depends('product_id', 'price_unit', 'price_subtotal', 'rate_per_rft', 'amount_taxed', 'tax_id', 'price_total', 'discount', 'disc_percentage')
    def _compute_amount_total(self):
        for line in self:
            disc_percentage = (line.amount_taxed / 100) * line.disc_percentage
            line.price_total =  line.amount_taxed - (line.discount + disc_percentage)

