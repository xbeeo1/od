from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError
from collections import defaultdict


class SsRods(models.Model):
    _name = "ss.rods"
    _description = "Ss Rods"
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

    ss_rods_line = fields.One2many("ss.rods.line", "order_id", string="")

    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')
    ], string="State", default='draft')

    def action_draft(self):
        self.state = "draft"

    def action_confirmed(self):
        self.state = "confirmed"

    def action_cancel(self):
        self.state = "cancel"

    @api.depends('total_amount', 'ss_rods_line', 'ss_rods_line.price_total')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.ss_rods_line:
                total_amount += line.price_total

            rec.total_amount = total_amount


    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('Only cancelled record. You can Delete!'))
            if not rec.env.user.has_group('ssol_od_estimation.group_order_estimation_delete_access'):
                raise UserError(_('You can not delete this Maintenance Record. Contact your administrator.'))
            else:
                return super(SsRods, self).unlink()


class SsRodsLine(models.Model):
    _name = 'ss.rods.line'


    order_id = fields.Many2one('ss.rods', string='SS Order Reference', required=True, ondelete='cascade')
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

    ss_round_size_mm = fields.Selection(string="Size (mm)",
                                        selection=[('2', '2'),
                                                   ('2.5', '2.5'), ('3', '3'),
                                                   ('3.5', '3.5'), ('4', '4'),
                                                   ('4.5', '4.5'), ('5', '5'),
                                                   ('5.5', '5.5'), ('6', '6'),
                                                   ('6.5', '6.5'), ('7', '7'),
                                                   ('8', '8'), ('9', '9'),
                                                   ('10', '10'), ('10.5', '10.5'),
                                                   ('11', '11'), ('12', '12'),
                                                   ('13', '13'), ('14', '14'),
                                                   ('15', '15'), ('16', '16'),
                                                   ('17', '17'), ('18', '18'),
                                                   ('19', '19'), ('20', '20'),
                                                   ('21', '21'), ('22', '22'),
                                                   ('24', '24'), ('25', '25'),
                                                   ('26', '26'), ('27', '27'),
                                                   ('28', '28'), ('30', '30'),
                                                   ('32', '32'), ('35', '35'),
                                                   ('36', '36'), ('38', '38'),
                                                   ('40', '40'), ('45', '45'),
                                                   ('50', '50'), ('55', '55'),
                                                   ('60', '60'), ('65', '65'),
                                                   ('70', '70'), ('75', '75'),
                                                   ('80', '80'), ('85', '85'),
                                                   ('90', '90'), ('95', '95'),
                                                   ('100', '100'), ('105', '105'),
                                                   ('110', '110'), ('115', '115'),
                                                   ('120', '120'), ('125', '125'),
                                                   ('130', '130'),('150', '150')],
                                        default='2')

    round_kgs_pft = fields.Float(string="Weight/ft (kg)", digits=(16, 4), compute='_compute_round_kgs_pft')
    length_fit = fields.Float(string='Length (ft)', required=True, digits='Product Unit of Measure', default=1)
    total_weight = fields.Float(string="Total Weight (kg)", digits=(16, 2), compute='_compute_total_round_kgs_pft')

    @api.depends('ss_round_size_mm', 'round_kgs_pft', 'product_id')
    def _compute_round_kgs_pft(self):
        for line in self:
            if line.ss_round_size_mm == '2':
                line.round_kgs_pft = 0.008

            elif line.ss_round_size_mm == '2.5':
                line.round_kgs_pft = 0.0012

            elif line.ss_round_size_mm == '3':
                line.round_kgs_pft = 0.0017

            elif line.ss_round_size_mm == '3.5':
                line.round_kgs_pft = 0.023

            elif line.ss_round_size_mm == '4':
                line.round_kgs_pft = 0.030

            elif line.ss_round_size_mm == '4.5':
                line.round_kgs_pft = 0.038

            elif line.ss_round_size_mm == '5':
                line.round_kgs_pft = 0.048

            elif line.ss_round_size_mm == '5.5':
                line.round_kgs_pft = 0.057

            elif line.ss_round_size_mm == '6':
                line.round_kgs_pft = 0.068

            elif line.ss_round_size_mm == '6.5':
                line.round_kgs_pft = 0.080

            elif line.ss_round_size_mm == '7':
                line.round_kgs_pft = 0.093

            elif line.ss_round_size_mm == '8':
                line.round_kgs_pft = 0.122

            elif line.ss_round_size_mm == '9':
                line.round_kgs_pft = 0.154

            elif line.ss_round_size_mm == '10':
                line.round_kgs_pft = 0.190

            elif line.ss_round_size_mm == '10.5':
                line.round_kgs_pft = 0.209

            elif line.ss_round_size_mm == '11':
                line.round_kgs_pft = 0.230

            elif line.ss_round_size_mm == '12':
                line.round_kgs_pft = 0.274

            elif line.ss_round_size_mm == '13':
                line.round_kgs_pft = 0.321

            elif line.ss_round_size_mm == '14':
                line.round_kgs_pft = 0.373

            elif line.ss_round_size_mm == '15':
                line.round_kgs_pft = 0.426

            elif line.ss_round_size_mm == '16':
                line.round_kgs_pft = 0.486

            elif line.ss_round_size_mm == '17':
                line.round_kgs_pft = 0.549

            elif line.ss_round_size_mm == '18':
                line.round_kgs_pft = 0.616

            elif line.ss_round_size_mm == '19':
                line.round_kgs_pft = 0.685

            elif line.ss_round_size_mm == '20':
                line.round_kgs_pft = 0.760

            elif line.ss_round_size_mm == '21':
                line.round_kgs_pft = 0.838

            elif line.ss_round_size_mm == '22':
                line.round_kgs_pft = 0.920

            elif line.ss_round_size_mm == '24':
                line.round_kgs_pft = 1.094

            elif line.ss_round_size_mm == '25':
                line.round_kgs_pft = 1.188

            elif line.ss_round_size_mm == '26':
                line.round_kgs_pft = 1.284

            elif line.ss_round_size_mm == '27':
                line.round_kgs_pft = 1.385

            elif line.ss_round_size_mm == '28':
                line.round_kgs_pft = 1.490

            elif line.ss_round_size_mm == '30':
                line.round_kgs_pft = 1.710

            elif line.ss_round_size_mm == '32':
                line.round_kgs_pft = 1.946

            elif line.ss_round_size_mm == '35':
                line.round_kgs_pft = 2.328

            elif line.ss_round_size_mm == '36':
                line.round_kgs_pft = 2.462

            elif line.ss_round_size_mm == '38':
                line.round_kgs_pft = 2.744

            elif line.ss_round_size_mm == '40':
                line.round_kgs_pft = 3.040

            elif line.ss_round_size_mm == '45':
                line.round_kgs_pft = 3.848

            elif line.ss_round_size_mm == '50':
                line.round_kgs_pft = 4.750

            elif line.ss_round_size_mm == '55':
                line.round_kgs_pft = 5.748

            elif line.ss_round_size_mm == '60':
                line.round_kgs_pft = 6.840

            elif line.ss_round_size_mm == '65':
                line.round_kgs_pft = 8.028

            elif line.ss_round_size_mm == '70':
                line.round_kgs_pft = 9.310

            elif line.ss_round_size_mm == '75':
                line.round_kgs_pft = 10.688

            elif line.ss_round_size_mm == '80':
                line.round_kgs_pft = 12.160

            elif line.ss_round_size_mm == '85':
                line.round_kgs_pft = 13.728

            elif line.ss_round_size_mm == '90':
                line.round_kgs_pft = 15.390

            elif line.ss_round_size_mm == '95':
                line.round_kgs_pft = 17.148

            elif line.ss_round_size_mm == '100':
                line.round_kgs_pft = 19.000

            elif line.ss_round_size_mm == '105':
                line.round_kgs_pft = 20.948

            elif line.ss_round_size_mm == '110':
                line.round_kgs_pft = 22.990

            elif line.ss_round_size_mm == '115':
                line.round_kgs_pft = 25.128

            elif line.ss_round_size_mm == '120':
                line.round_kgs_pft = 27.360

            elif line.ss_round_size_mm == '125':
                line.round_kgs_pft = 29.688

            elif line.ss_round_size_mm == '130':
                line.round_kgs_pft = 32.110

            elif line.ss_round_size_mm == '150':
                line.round_kgs_pft = 42.750

            else:
                line.round_kgs_pft = False


    @api.depends('total_weight', 'round_kgs_pft', 'length_fit', 'ss_round_size_mm', 'product_id')
    def _compute_total_round_kgs_pft(self):
        for line in self:
            line.total_weight = line.round_kgs_pft * line.length_fit



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
    @api.depends('order_id.ss_rods_line', 'sr_no', 'sr_no_char')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            value_sr = 1
            for line in order.ss_rods_line:
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

