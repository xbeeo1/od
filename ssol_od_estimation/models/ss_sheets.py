from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError
from collections import defaultdict


class SsSheets(models.Model):
    _name = "ss.sheets"
    _description = "Ss Sheets"
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

    ss_sheets_line = fields.One2many("ss.sheets.line", "order_id", string="")

    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')
    ], string="State", default='draft')

    def action_draft(self):
        self.state = "draft"

    def action_confirmed(self):
        self.state = "confirmed"

    def action_cancel(self):
        self.state = "cancel"

    @api.depends('total_amount', 'ss_sheets_line', 'ss_sheets_line.price_total')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.ss_sheets_line:
                total_amount += line.price_total

            rec.total_amount = total_amount


    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('Only cancelled record. You can Delete!'))
            if not rec.env.user.has_group('ssol_od_estimation.group_order_estimation_delete_access'):
                raise UserError(_('You can not delete this Maintenance Record. Contact your administrator.'))
            else:
                return super(SsSheets, self).unlink()


class SsSheetsLine(models.Model):
    _name = 'ss.sheets.line'


    order_id = fields.Many2one('ss.sheets', string='SS Order Reference', required=True, ondelete='cascade')
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

    ss_sheets_size_mm = fields.Selection(string="MM",
                                        selection=[('0.3', '0.3'),
                                                   ('0.4', '0.4'), ('0.5', '0.5'),
                                                   ('0.6', '0.6'), ('0.7', '0.7'),
                                                   ('0.8', '0.8'), ('0.9', '0.9'),
                                                   ('1', '1'), ('1.2', '1.2'),
                                                   ('1.6', '1.6'),('2.1', '2.1'), ('2.6', '2.6'),
                                                   ('3', '3'), ('3.25', '3.25'),
                                                   ('4', '4'), ('4.5', '4.5'),
                                                   ('6', '6'), ('6.25(1/4")', '6.25(1/4")'),
                                                   ('8', '8'), ('9', '9'),
                                                   ('10', '10'), ('12', '12'),
                                                   ('12.5(1/2")', '12.5(1/2")'),
                                                   ('16', '16'), ('19', '19'),
                                                   ('25', '25')], default='0.3')

    swg_ss_sheet = fields.Integer(string="SWG", compute='_compute_swg_ss_sheet')
    weight_sqft_kgs = fields.Float(string="W.Sqft/Kg", digits=(16, 3), compute='_compute_weight_sqft_kgs')
    length = fields.Float(string="Length (ft)")
    width = fields.Float(string="Width (ft)")
    sqft = fields.Float(string="Sqft's", compute='_compute_sqft')
    total_weight = fields.Float(string="Total W.Sqft/Kg", digits=(16, 2), compute='_compute_total_weight_sqft_kgs')

    @api.depends('ss_sheets_size_mm', 'weight_sqft_kgs', 'product_id')
    def _compute_weight_sqft_kgs(self):
        for line in self:
            if line.ss_sheets_size_mm == '0.3':
                line.weight_sqft_kgs = 0.230

            elif line.ss_sheets_size_mm == '0.4':
                line.weight_sqft_kgs = 0.285

            elif line.ss_sheets_size_mm == '0.5':
                line.weight_sqft_kgs = 0.360

            elif line.ss_sheets_size_mm == '0.6':
                line.weight_sqft_kgs = 0.450

            elif line.ss_sheets_size_mm == '0.7':
                line.weight_sqft_kgs = 0.570

            elif line.ss_sheets_size_mm == '0.8':
                line.weight_sqft_kgs = 0.630

            elif line.ss_sheets_size_mm == '0.9':
                line.weight_sqft_kgs = 0.680

            elif line.ss_sheets_size_mm == '1':
                line.weight_sqft_kgs = 0.790

            elif line.ss_sheets_size_mm == '1.2':
                line.weight_sqft_kgs = 0.900

            elif line.ss_sheets_size_mm == '1.6':
                line.weight_sqft_kgs = 1.15


            elif line.ss_sheets_size_mm == '2.1':
                line.weight_sqft_kgs = 1.45

            elif line.ss_sheets_size_mm == '2.6':
                line.weight_sqft_kgs = 2.00

            elif line.ss_sheets_size_mm == '3':
                line.weight_sqft_kgs = 2.18

            elif line.ss_sheets_size_mm == '3.25':
                line.weight_sqft_kgs = 2.56

            elif line.ss_sheets_size_mm == '4':
                line.weight_sqft_kgs = 3.00

            elif line.ss_sheets_size_mm == '4.5':
                line.weight_sqft_kgs = 3.5

            elif line.ss_sheets_size_mm == '6':
                line.weight_sqft_kgs = 4.55

            elif line.ss_sheets_size_mm == '6.25(1/4")':
                line.weight_sqft_kgs = 4.63

            elif line.ss_sheets_size_mm == '8':
                line.weight_sqft_kgs = 6.00

            elif line.ss_sheets_size_mm == '9':
                line.weight_sqft_kgs = 6.87

            elif line.ss_sheets_size_mm == '10':
                line.weight_sqft_kgs = 7.8

            elif line.ss_sheets_size_mm == '12':
                line.weight_sqft_kgs = 9.36

            elif line.ss_sheets_size_mm == '12.5(1/2")':
                line.weight_sqft_kgs = 9.75

            elif line.ss_sheets_size_mm == '16':
                line.weight_sqft_kgs = 12.48

            elif line.ss_sheets_size_mm == '19':
                line.weight_sqft_kgs = 14.82

            elif line.ss_sheets_size_mm == '25':
                line.weight_sqft_kgs = 19.500

            else:
                line.weight_sqft_kgs = False

    @api.depends('swg_ss_sheet', 'ss_sheets_size_mm', 'product_id')
    def _compute_swg_ss_sheet(self):
        for line in self:
            if line.ss_sheets_size_mm == '0.3':
                line.swg_ss_sheet = 30

            elif line.ss_sheets_size_mm == '0.4':
                line.swg_ss_sheet = 28

            elif line.ss_sheets_size_mm == '0.5':
                line.swg_ss_sheet = 25

            elif line.ss_sheets_size_mm == '0.6':
                line.swg_ss_sheet = 24

            elif line.ss_sheets_size_mm == '0.7':
                line.swg_ss_sheet = 22

            elif line.ss_sheets_size_mm == '0.8':
                line.swg_ss_sheet = 21

            elif line.ss_sheets_size_mm == '0.9':
                line.swg_ss_sheet = 20

            elif line.ss_sheets_size_mm == '1':
                line.swg_ss_sheet = 19

            elif line.ss_sheets_size_mm == '1.2':
                line.swg_ss_sheet = 18

            elif line.ss_sheets_size_mm == '1.6':
                line.swg_ss_sheet = 16

            elif line.ss_sheets_size_mm == '2.1':
                line.swg_ss_sheet = 14

            elif line.ss_sheets_size_mm == '2.6':
                line.swg_ss_sheet = 12

            elif line.ss_sheets_size_mm == '3':
                line.swg_ss_sheet = 11

            elif line.ss_sheets_size_mm == '3.25':
                line.swg_ss_sheet = 10

            elif line.ss_sheets_size_mm == '4':
                line.swg_ss_sheet = 8

            elif line.ss_sheets_size_mm == '4.5':
                line.swg_ss_sheet = 6

            else:
                line.swg_ss_sheet = False


    @api.depends('sqft', 'length', 'width', 'product_id')
    def _compute_sqft(self):
        for line in self:
            if line.length and line.width:
                line.sqft = line.length * line.width
            else:
                line.sqft = False

    @api.depends('total_weight', 'weight_sqft_kgs', 'sqft', 'ss_sheets_size_mm', 'product_id', 'length', 'width')
    def _compute_total_weight_sqft_kgs(self):
        for line in self:

            if line.length and line.width:
                total_weight_sqft = (line.length * line.width)
                line.total_weight = line.weight_sqft_kgs * total_weight_sqft
            else:
                line.total_weight = False


            # line.total_weight = line.sqft * line.weight_sqft_kgs



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
    @api.depends('order_id.ss_sheets_line', 'sr_no', 'sr_no_char')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            value_sr = 1
            for line in order.ss_sheets_line:
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

