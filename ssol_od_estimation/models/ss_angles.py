from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError
from collections import defaultdict


class SsAngles(models.Model):
    _name = "ss.angles"
    _description = "Ss Angles"
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

    ss_angles_line = fields.One2many("ss.angles.line", "order_id", string="")

    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')
    ], string="State", default='draft')

    def action_draft(self):
        self.state = "draft"

    def action_confirmed(self):
        self.state = "confirmed"

    def action_cancel(self):
        self.state = "cancel"

    @api.depends('total_amount', 'ss_angles_line', 'ss_angles_line.price_total')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.ss_angles_line:
                total_amount += line.price_total

            rec.total_amount = total_amount


    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('Only cancelled record. You can Delete!'))
            if not rec.env.user.has_group('ssol_od_estimation.group_order_estimation_delete_access'):
                raise UserError(_('You can not delete this Maintenance Record. Contact your administrator.'))
            else:
                return super(SsAngles, self).unlink()


class SsAnglesLine(models.Model):
    _name = 'ss.angles.line'


    order_id = fields.Many2one('ss.angles', string='SS Order Reference', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='order_id.company_id', store=True, index=True)
    product_id = fields.Many2one(comodel_name='product.product', check_company=True, domain=lambda self: self._product_id_domain())
    sr_no = fields.Integer(string="Sr No.", compute='_compute_sr_no', store=True)
    sr_no_char = fields.Char(string="Sr No.", compute='_compute_sr_no', store=True)
    name = fields.Text(string="Description", compute='_compute_name',  store=True)

    product_uom_id = fields.Many2one(comodel_name='uom.uom', string="Unit of Measure", compute='_compute_product_uom_id',
        store=True, readonly=False, precompute=True,
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_uom_qty = fields.Float(string='Qty', required=True, digits='Product Unit of Measure', default=1)

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

    ss_angles_size_inches = fields.Selection(string="Size x Size in Inches",
                                           selection=[('1.1/2"x1.1/2"x1/8"', '1.1/2"x1.1/2"x1/8"'),
                                                      ('1.1/2"x1.1/2"x3/16"', '1.1/2"x1.1/2"x3/16"'),
                                                      ('1.1/2"x1.1/2"x1/4"', '1.1/2"x1.1/2"x1/4"'),
                                                      ('1.1/2"x1.1/2"x5/16"', '1.1/2"x1.1/2"x5/16"'),
                                                      ('1.1/2"x1.1/2"x3/8"', '1.1/2"x1.1/2"x3/8"'),
                                                      ('2" x 2" x3/16', '2" x 2" x3/16'),
                                                      ('2" x 2" x1/4', '2" x 2" x1/4'),
                                                      ('2" x 2" x5/16', '2" x 2" x5/16'),
                                                      ('2" x 1/2" x3/8', '2" x 1/2" x3/8'),
                                                      ('2" x 1/2" x1/2', '2" x 1/2" x1/2'),
                                                      ('2.1/2"x2.1/2"x1/4"', '2.1/2"x2.1/2"x1/4"'),
                                                      ('2.1/2"x2.1/2"x5/16"', '2.1/2"x2.1/2"x5/16"'),
                                                      ('2.1/2"x2.1/2"X3/8"', '2.1/2"x2.1/2"X3/8"'),
                                                      ('2.1/2"X2.1/2"X1/2"', '2.1/2"X2.1/2"X1/2"'),
                                                      ('3" X 3" X1/4"', '3" X 3" X1/4"'),
                                                      ('3" X 3" X5/16"', '3" X 3" X5/16"'),
                                                      ('3" X 3" X3/8"', '3" X 3" X3/8"'),
                                                      ('3" X 3" X1/2"', '3" X 3" X1/2"'),
                                                      ('3" X 3" X5/8"', '3" X 3" X5/8"'),
                                                      ('4" X 4" X3/8"', '4" X 4" X3/8"'),
                                                      ('4" X 4" X1/2"', '4" X 4" X1/2"'),
                                                      ('4" X 4" X5/8"', '4" X 4" X5/8"'),
                                                      ('4" X 4" X3/4"', '4" X 4" X3/4"')],
                                           default='1.1/2"x1.1/2"x1/8"')

    weight_kgs_pft = fields.Float(string="Weight/ft (Kg)", digits=(16, 3), compute='_compute_weight_kgs_pft')
    quantity = fields.Float(string="Length (ft)")
    length_fit = fields.Float(string='Qty', required=True, digits='Product Unit of Measure', default=1)
    total_weight = fields.Float(string="Total Weight (kg)", digits=(16, 2), compute='_compute_total_weight')

    @api.depends('ss_angles_size_inches', 'weight_kgs_pft', 'product_id')
    def _compute_weight_kgs_pft(self):
        for line in self:
            if line.ss_angles_size_inches == '1.1/2"x1.1/2"x1/8"':
                line.weight_kgs_pft = 0.560

            elif line.ss_angles_size_inches == '1.1/2"x1.1/2"x3/16"':
                line.weight_kgs_pft = 0.810


            elif line.ss_angles_size_inches == '1.1/2"x1.1/2"x1/4"':
                line.weight_kgs_pft = 1.060

            elif line.ss_angles_size_inches == '1.1/2"x1.1/2"x5/16"':
                line.weight_kgs_pft = 1.300

            elif line.ss_angles_size_inches == '1.1/2"x1.1/2"x3/8"':
                line.weight_kgs_pft = 1.520

            elif line.ss_angles_size_inches == '2" x 2" x3/16':
                line.weight_kgs_pft = 1.100

            elif line.ss_angles_size_inches == '2" x 2" x1/4':
                line.weight_kgs_pft = 1.450

            elif line.ss_angles_size_inches == '2" x 2" x5/16':
                line.weight_kgs_pft = 1.780

            elif line.ss_angles_size_inches == '2" x 1/2" x3/8':
                line.weight_kgs_pft = 2.100

            elif line.ss_angles_size_inches == '2" x 1/2" x1/2':
                line.weight_kgs_pft = 4.510

            elif line.ss_angles_size_inches == '2.1/2"x2.1/2"x1/4"':
                line.weight_kgs_pft = 1.830

            elif line.ss_angles_size_inches == '2.1/2"x2.1/2"x5/16"':
                line.weight_kgs_pft = 2.260

            elif line.ss_angles_size_inches == '2.1/2"x2.1/2"X3/8"':
                line.weight_kgs_pft = 2.670

            elif line.ss_angles_size_inches == '2.1/2"X2.1/2"X1/2"':
                line.weight_kgs_pft = 3.470

            elif line.ss_angles_size_inches == '3" X 3" X1/4"':
                line.weight_kgs_pft = 2.220

            elif line.ss_angles_size_inches == '3" X 3" X5/16"':
                line.weight_kgs_pft = 2.740

            elif line.ss_angles_size_inches == '3" X 3" X3/8"':
                line.weight_kgs_pft = 3.260

            elif line.ss_angles_size_inches == '3" X 3" X1/2"':
                line.weight_kgs_pft = 4.250

            elif line.ss_angles_size_inches == '3" X 3" X5/8"':
                line.weight_kgs_pft = 5.180

            elif line.ss_angles_size_inches == '4" X 4" X3/8"':
                line.weight_kgs_pft = 4.340

            elif line.ss_angles_size_inches == '4" X 4" X1/2"':
                line.weight_kgs_pft = 5.780

            elif line.ss_angles_size_inches == '4" X 4" X5/8"':
                line.weight_kgs_pft = 7.110

            elif line.ss_angles_size_inches == '4" X 4" X3/4"':
                line.weight_kgs_pft = 8.390


            elif line.ss_angles_size_inches == '':
                line.weight_kgs_pft = 0








            else:
                line.weight_kgs_pft = False


    @api.depends('total_weight', 'weight_kgs_pft', 'quantity', 'length_fit','ss_angles_size_inches', 'product_id')
    def _compute_total_weight(self):
        for line in self:
            line.total_weight = line.weight_kgs_pft * line.quantity * line.length_fit



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
    @api.depends('order_id.ss_angles_line', 'sr_no', 'sr_no_char')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            value_sr = 1
            for line in order.ss_angles_line:
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

