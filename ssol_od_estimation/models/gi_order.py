from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError
from collections import defaultdict


class GiOrder(models.Model):
    _name = "gi.order"
    _description = "Order Estimation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "parent_order_id"

    parent_order_id = fields.Many2one('order.estimation', string='Parent Order', tracking=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True, related='parent_order_id.partner_id')
    total_amount = fields.Float(string="Total Amount", tracking=True, compute='_compute_total_amount')
    order_date = fields.Date("Date", tracking=True, default=date.today())
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user.id, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, readonly=True)
    attachment = fields.Binary(string="Attachment", tracking=True)
    description = fields.Text(string="Note", tracking=True)

    active = fields.Boolean(string="Active", default=True)
    image_1920 = fields.Binary(string='Image')

    gi_order_line = fields.One2many("gi.order.line", "order_id", string="")

    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')
    ], string="State", default='draft')


    def action_draft(self):
        self.state = "draft"

    def action_confirmed(self):
        self.state = "confirmed"

    def action_cancel(self):
        self.state = "cancel"


    @api.depends('total_amount', 'gi_order_line', 'gi_order_line.price_total')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.gi_order_line:
                total_amount += line.price_total

            rec.total_amount = total_amount

    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('Only cancelled record. You can Delete!'))
            if not rec.env.user.has_group('ssol_od_estimation.group_order_estimation_delete_access'):
                raise UserError(_('You can not delete this Maintenance Record. Contact your administrator.'))
            else:
                return super(GiOrder, self).unlink()


class GiOrderLine(models.Model):
    _name = 'gi.order.line'


    order_id = fields.Many2one('gi.order', string='Gi Order Reference', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='order_id.company_id', store=True, index=True)
    product_id = fields.Many2one(comodel_name='product.product', check_company=True, domain=lambda self: self._product_id_domain())
    sr_no = fields.Integer(string="Sr No.", compute='_compute_sr_no', store=True)
    sr_no_char = fields.Char(string="Sr No.", compute='_compute_sr_no', store=True)
    name = fields.Text(string="Description",  store=True)

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

    swg = fields.Selection(string="SWG", selection=[
        ('10', '10'), ('11', '11'), ('12', '12'),
        ('13', '13'), ('14', '14'), ('15', '15'),
        ('16', '16'), ('17', '17'), ('18', '18'),
        ('19', '19'), ('20', '20'), ('21', '21'),
        ('22', '22'), ('23', '23'), ('24', '24'),
        ('25', '25'), ('26', '26'), ('27', '27'),
        ('28', '28'), ('29', '29'), ('30', '30'),
        ('31', '31'), ('32', '32'), ('33', '33'),
        ('34', '34'), ('35', '35'), ('36', '36')], default='10')

    thickness = fields.Selection(string="Thickness", selection=[
        ('3.18', '3.18'), ('2.83', '2.83'), ('2.52', '2.52'),
        ('2.24', '2.24'), ('1.99', '1.99'), ('1.59', '1.59'),
        ('1.77', '1.77'), ('1.41', '1.41'), ('1.26', '1.26'),
        ('1.2', '1.2'), ('1', '1'), ('0.89', '0.89'),
        ('0.79', '0.79'), ('0.71', '0.71'), ('0.63', '0.63'),
        ('0.56', '0.56'), ('0.5', '0.5'), ('0.44', '0.44'),
        ('0.4', '0.4'), ('0.35', '0.35'), ('0.31', '0.31'),
        ('0.28', '0.28'), ('0.25', '0.25'), ('0.22', '0.22'),
        ('0.2', '0.2'), ('0.18', '0.18'), ('0.15', '0.15')], compute='_compute_thickness_wight')

    length = fields.Float(string="Length (ft)")
    width = fields.Float(string="Width (ft)")
    product_uom_qty = fields.Float(string='Qty', store=True, default=1)
    sqft = fields.Float(string="Sqft")
    total_sqft = fields.Float(string="Total (Sqft)", compute='_compute_total_sqft')
    weight_per_sheet = fields.Float(string="Weight/Piece (Kg)", compute='_compute_weight_per_sheet')
    weight_per_sqft = fields.Float(string="WPSQFT", compute='_compute_thickness_wight', digits=(16, 2))
    total_weight = fields.Float(string="Total Weight (kg)", compute='_compute_total_weight', digits=(16, 2))

    @api.depends('thickness', 'weight_per_sqft', 'swg', 'product_id')
    def _compute_thickness_wight(self):
        for line in self:

            if line.swg == '10':
                line.thickness = '3.18'
                line.weight_per_sqft = 2.318

            elif line.swg == '11':
                line.thickness = '2.83'
                line.weight_per_sqft = 2.063

            elif line.swg == '12':
                line.thickness = '2.52'
                line.weight_per_sqft = 1.835

            elif line.swg == '13':
                line.thickness = '2.24'
                line.weight_per_sqft = 1.636

            elif line.swg == '14':
                line.thickness = '1.99'
                line.weight_per_sqft = 1.454

            elif line.swg == '15':
                line.thickness = '1.77'
                line.weight_per_sqft = 1.295

            elif line.swg == '16':
                line.thickness = '1.59'
                line.weight_per_sqft = 1.1590625

            elif line.swg == '17':
                line.thickness = '1.41'
                line.weight_per_sqft = 1.0318125

            elif line.swg == '18':
                line.thickness = '1.26'
                line.weight_per_sqft = 0.91815625

            elif line.swg == '19':
                line.thickness = '1.2'
                line.weight_per_sqft = 0.813625

            elif line.swg == '20':
                line.thickness = '1'
                line.weight_per_sqft = 0.72725

            elif line.swg == '21':
                line.thickness = '0.89'
                line.weight_per_sqft = 0.6454375

            elif line.swg == '22':
                line.thickness = '0.79'
                line.weight_per_sqft = 0.57725

            elif line.swg == '23':
                line.thickness = '0.71'
                line.weight_per_sqft = 0.513625

            elif line.swg == '24':
                line.thickness = '0.63'
                line.weight_per_sqft = 0.4590625

            elif line.swg == '25':
                line.thickness = '0.56'
                line.weight_per_sqft = 0.40865625

            elif line.swg == '26':
                line.thickness = '0.5'
                line.weight_per_sqft = 0.363625

            elif line.swg == '27':
                line.thickness = '0.44'
                line.weight_per_sqft = 0.32328125

            elif line.swg == '28':
                line.thickness = '0.4'
                line.weight_per_sqft = 0.28946875

            elif line.swg == '29':
                line.thickness = '0.35'
                line.weight_per_sqft = 0.25765625

            elif line.swg == '30':
                line.thickness = '0.31'
                line.weight_per_sqft = 0.228125

            elif line.swg == '31':
                line.thickness = '0.28'
                line.weight_per_sqft = 0.20409375

            elif line.swg == '32':
                line.thickness = '0.25'
                line.weight_per_sqft = 0.1715625

            elif line.swg == '33':
                line.thickness = '0.22'
                line.weight_per_sqft = 0.16134375

            elif line.swg == '34':
                line.thickness = '0.2'
                line.weight_per_sqft = 0.14275

            elif line.swg == '35':
                line.thickness = '0.18'
                line.weight_per_sqft = 0.128125

            elif line.swg == '36':
                line.thickness = '0.15'
                line.weight_per_sqft = 0.10325

            else:
                line.thickness = False
                line.weight_per_sqft = False

            # print('swg', line.swg, 'thickness', line.thickness)

    @api.depends('length', 'width', 'product_id', 'total_sqft', 'product_uom_qty')
    def _compute_total_sqft(self):
        for line in self:
            if line.length and line.width:
                line.total_sqft = (line.length * line.width) * line.product_uom_qty
            else:
                line.total_sqft = False

    @api.depends('length', 'width', 'product_id', 'total_sqft', 'product_uom_qty', 'weight_per_sheet', 'total_weight')
    def _compute_weight_per_sheet(self):
        for line in self:
            if line.product_uom_qty and line.total_weight:
                line.weight_per_sheet = line.total_weight / line.product_uom_qty
            else:
                line.weight_per_sheet = False


    @api.depends('swg', 'weight_per_sqft', 'total_weight', 'total_sqft', 'length', 'width', 'product_id',
                 'total_weight')
    def _compute_total_weight(self):
        for line in self:
            if line.total_sqft:
                line.total_weight = line.total_sqft * line.weight_per_sqft
            else:
                line.total_weight = False


    # === COMPUTE METHODS ===#
    # @api.depends('product_id')
    # def _compute_name(self):
    #     for option in self:
    #         if not option.product_id:
    #             continue
    #         option.name = option.product_id.get_product_multiline_description_sale()

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

    @api.depends('total_amount', 'order_estimation_line', 'order_estimation_line.price_total')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.order_estimation_line:
                total_amount += line.price_total

            rec.total_amount = total_amount


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
    @api.depends('order_id.gi_order_line', 'sr_no', 'sr_no_char')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            value_sr = 1
            for line in order.gi_order_line:
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


    @api.depends('product_id', 'price_unit', 'price_subtotal', 'total_weight', 'amount_taxed', 'tax_id',
                 'price_total', 'discount', 'disc_percentage')
    def _compute_amount_total(self):
        for line in self:
            disc_percentage = (line.amount_taxed / 100) * line.disc_percentage
            line.price_total = line.amount_taxed - (line.discount + disc_percentage)

