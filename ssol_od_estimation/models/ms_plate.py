from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError
from collections import defaultdict


class MsPlate(models.Model):
    _name = "ms.plate"
    _description = "Ms Plate"
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

    ms_plate_line = fields.One2many("ms.plate.line", "order_id", string="")

    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')
    ], string="State", default='draft')

    def action_draft(self):
        self.state = "draft"

    def action_confirmed(self):
        self.state = "confirmed"

    def action_cancel(self):
        self.state = "cancel"

    @api.depends('total_amount', 'ms_plate_line', 'ms_plate_line.price_total')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.ms_plate_line:
                total_amount += line.price_total

            rec.total_amount = total_amount

    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('Only cancelled record. You can Delete!'))
            if not rec.env.user.has_group('ssol_od_estimation.group_order_estimation_delete_access'):
                raise UserError(_('You can not delete this Maintenance Record. Contact your administrator.'))
            else:
                return super(MsPlate, self).unlink()


class MsChannelLine(models.Model):
    _name = 'ms.plate.line'


    order_id = fields.Many2one('ms.plate', string='Estimation Order Reference', required=True, ondelete='cascade')
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
    price_unit = fields.Monetary(string="Unit price")
    price_subtotal = fields.Monetary(string="Subtotal", compute='_compute_price_subtotal')
    cost_price = fields.Monetary(string='Cost', currency_field='currency_id', compute='_compute_cost_margin')
    profit_margin = fields.Monetary(string='Margin', currency_field='currency_id', compute='_compute_cost_margin')
    tax_id = fields.Many2many('account.tax', string="Taxes", store=True, context={'active_test': False}, check_company=True)
    discount = fields.Monetary(string="Discount")
    disc_percentage = fields.Monetary(string="Disc%")
    amount_taxed = fields.Monetary(string="Tax Excl.", compute='_compute_amount_taxed')
    price_total = fields.Monetary(string="Tax Incl.", compute='_compute_amount_total')

    ms_plate_size = fields.Selection(string="Size", selection=[('3 (mm)', '3 (mm)'),
                                                               ('4 (mm)', '4 (mm)'),
                                                               ('5 (mm)', '5 (mm)'),
                                                               ('6 (mm)', '6 (mm)'),
                                                               ('8 (mm)', '8 (mm)'),
                                                               ('9 (mm)', '9 (mm)'),
                                                               ('10 (mm)', '10 (mm)'),
                                                               ('12 (mm)', '12 (mm)'),
                                                               ('16 (mm)', '16 (mm)'),
                                                               ('20 (mm)', '20 (mm)'),
                                                               ('25 (mm)', '25 (mm)'),
                                                               ], default='3 (mm)')

    length = fields.Float(string="Length (ft)", default=4, readonly=False)
    width = fields.Float(string="Width (ft)", default=8, readonly=False)
    product_uom_qty = fields.Float(string='Qty', store=True, default=1)
    weight_per_sqft = fields.Float(string="Weight/Sqft (kg)", digits=(16, 5), compute='_compute_weight_per_sqft')
    weight_fit = fields.Float(string="Weight/Sheet (kg)", digits=(16, 4), compute='_compute_total_weight_fit')
    total_weight = fields.Float(string="Total Weight (kg)", digits=(16, 2), compute='_compute_total_weight')

    @api.depends('ms_plate_size', 'length', 'width', 'weight_fit', 'total_weight', 'product_id', 'weight_per_sqft')
    def _compute_weight_per_sqft(self):
        for line in self:
            if line.ms_plate_size == '3 (mm)':
                line.weight_per_sqft = 2.40625

            elif line.ms_plate_size == '4 (mm)':
                line.weight_per_sqft = 2.96875

            elif line.ms_plate_size == '5 (mm)':
                line.weight_per_sqft = 3.65625

            elif line.ms_plate_size == '6 (mm)':
                line.weight_per_sqft = 4.53125

            elif line.ms_plate_size == '8 (mm)':
                line.weight_per_sqft = 5.9375

            elif line.ms_plate_size == '9 (mm)':
                line.weight_per_sqft = 6.5625

            elif line.ms_plate_size == '10 (mm)':
                line.weight_per_sqft = 7.34375

            elif line.ms_plate_size == '12 (mm)':
                line.weight_per_sqft = 9.6875

            elif line.ms_plate_size == '16 (mm)':
                line.weight_per_sqft = 12.1875

            elif line.ms_plate_size == '20 (mm)':
                line.weight_per_sqft = 14.8438

            elif line.ms_plate_size == '25 (mm)':
                line.weight_per_sqft = 19.6875

            else:
                line.weight_per_sqft = False

    @api.depends('total_weight', 'weight_fit', 'weight_fit', 'ms_plate_size', 'product_id', 'length', 'width',
                 'weight_fit', 'product_uom_qty', 'weight_per_sqft')
    def _compute_total_weight(self):
        for line in self:
            if line.length and line.width:
                total_sqft = (line.length * line.width) * line.product_uom_qty
                total_weight = total_sqft * line.weight_per_sqft
                line.total_weight = total_weight
            else:
                line.total_weight = False

    @api.depends('total_weight', 'weight_fit', 'weight_fit', 'ms_plate_size', 'product_id', 'length', 'width',
                 'weight_fit', 'product_uom_qty', 'weight_per_sqft')
    def _compute_total_weight_fit(self):
        for line in self:
            if line.total_weight:
                line.weight_fit = line.total_weight / line.product_uom_qty
            else:
                line.weight_fit = False



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
    @api.depends('order_id.ms_plate_line', 'sr_no', 'sr_no_char')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            value_sr = 1
            for line in order.ms_plate_line:
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

