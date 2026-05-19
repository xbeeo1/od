from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError
from collections import defaultdict
import math


class MsPipe(models.Model):
    _name = "ms.pipe"
    _description = "Ms pipe"
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

    ms_pipe_line = fields.One2many("ms.pipe.line", "order_id", string="")

    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')
    ], string="State", default='draft')

    def action_draft(self):
        self.state = "draft"

    def action_confirmed(self):
        self.state = "confirmed"

    def action_cancel(self):
        self.state = "cancel"


    @api.depends('total_amount', 'ms_pipe_line', 'ms_pipe_line.price_total')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.ms_pipe_line:
                total_amount += line.price_total

            rec.total_amount = total_amount

    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('Only cancelled record. You can Delete!'))
            if not rec.env.user.has_group('ssol_od_estimation.group_order_estimation_delete_access'):
                raise UserError(_('You can not delete this Maintenance Record. Contact your administrator.'))
            else:
                return super(MsPipe, self).unlink()


class MsPipeLine(models.Model):
    _name = 'ms.pipe.line'


    order_id = fields.Many2one('ms.pipe', string='Estimation Order Reference', required=True, ondelete='cascade')
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

    ms_pipe_size = fields.Selection(string="NB/MM (Inches)",
                                     selection=[('15(1/2")', '15__________(1/2")'),
                                                ('20(3/4")','20__________(3/4")'),
                                                ('25(1")', '25__________(1")'),
                                                ('32(1/4")', '32__________(1/4")'),
                                                ('40(1/2")', '40__________(1/2")'),
                                                ('50(2")', '50__________(2")'),
                                                ('65(2.1/2")', '65__________(2 1/2")'),
                                                ('80(3")', '80__________(3")'),
                                                ('90(3.1/2")', '90__________(3.1/2")'),
                                                ('100(4")', '100__________(4")'),
                                                ('125(5")', '125__________(5")'),
                                                ('150(6")', '150__________(6")'),
                                                ('200(8")', '200__________(8")'),
                                                ('250(10")', '250__________(10")'),
                                                ('300(12")', '300__________(12")'),
                                                ('350(14")', '350__________(14")'),
                                                ('400(16")', '400__________(16")'),
                                                ('450(18")', '450__________(18")'),
                                                ], default='15(1/2")')

    ms_pipe_medium = fields.Selection(string="Pipe Medium",
                                    selection=[('pipe_medium_20', 'SCH 20'),
                                               ('black_pipe_40', 'SCH 40'),
                                               ('black_pipe_80', 'SCH 80'),
                                               ('black_pipe_160', 'SCH 160'),
                                               ], default='pipe_medium_20')

    ms_pipe_weight_kg = fields.Float(string="Pipe/Weight (kg)", compute='_compute_ms_pipe_weight_kg')
    thickness = fields.Float(string="Th.", compute='_compute_thickness')
    rate_per_rft = fields.Float(string="Rate / Rft")
    product_uom_qty = fields.Float(string='Qty', compute='_compute_product_uom_qty')

    total_weight = fields.Float(string="Total Weight (Kg)", digits=(16, 2), compute='_compute_total_weight')

    @api.depends('total_weight', 'ms_pipe_medium', 'product_uom_qty', 'ms_pipe_weight_kg', 'product_id')
    def _compute_total_weight(self):
        for line in self:
            if line.product_uom_qty:
                line.total_weight = line.ms_pipe_weight_kg * line.product_uom_qty
                # line.total_weight = False
            else:
                line.total_weight = False

    @api.depends('ms_pipe_size', 'ms_pipe_medium')
    def _compute_ms_pipe_weight_kg(self):
        for line in self:

            if line.ms_pipe_medium == 'black_pipe_40':

                if line.ms_pipe_size == '15(1/2")':
                    line.ms_pipe_weight_kg = 7.85

                elif line.ms_pipe_size == '20(3/4")':
                    line.ms_pipe_weight_kg = 10.29

                elif line.ms_pipe_size == '25(1")':
                    line.ms_pipe_weight_kg = 15.26

                elif line.ms_pipe_size == '32(1/4")':
                    line.ms_pipe_weight_kg = 20.69

                elif line.ms_pipe_size == '40(1/2")':
                    line.ms_pipe_weight_kg = 24.71

                elif line.ms_pipe_size == '50(2")':
                    line.ms_pipe_weight_kg = 33.14

                elif line.ms_pipe_size == '65(2.1/2")':
                    line.ms_pipe_weight_kg = 52.65

                elif line.ms_pipe_size == '80(3")':
                    line.ms_pipe_weight_kg = 68.88

                elif line.ms_pipe_size == '90(3.1/2")':
                    line.ms_pipe_weight_kg = 82.77

                elif line.ms_pipe_size == '100(4")':
                    line.ms_pipe_weight_kg = 98.06

                elif line.ms_pipe_size == '125(5")':
                    line.ms_pipe_weight_kg = 132.77

                elif line.ms_pipe_size == '150(6")':
                    line.ms_pipe_weight_kg = 172.40

                elif line.ms_pipe_size == '200(8")':
                    line.ms_pipe_weight_kg = 259.53

                elif line.ms_pipe_size == '250(10")':
                    line.ms_pipe_weight_kg = 367.76

                elif line.ms_pipe_size == '300(12")':
                    line.ms_pipe_weight_kg = 486.19

                elif line.ms_pipe_size == '350(14")':
                    line.ms_pipe_weight_kg = 576.72

                elif line.ms_pipe_size == '400(16")':
                    line.ms_pipe_weight_kg = 752.13

                elif line.ms_pipe_size == '450(18")':
                    line.ms_pipe_weight_kg = 950.79

                else:
                    line.ms_pipe_weight_kg = False

            elif line.ms_pipe_medium == 'black_pipe_80':

                if line.ms_pipe_size == '15(1/2")':
                    line.ms_pipe_weight_kg = 9.86

                elif line.ms_pipe_size == '20(3/4")':
                    line.ms_pipe_weight_kg = 13.40

                elif line.ms_pipe_size == '25(1")':
                    line.ms_pipe_weight_kg = 19.74

                elif line.ms_pipe_size == '32(1/4")':
                    line.ms_pipe_weight_kg = 27.25

                elif line.ms_pipe_size == '40(1/2")':
                    line.ms_pipe_weight_kg = 33.03

                elif line.ms_pipe_size == '50(2")':
                    line.ms_pipe_weight_kg = 45.64

                elif line.ms_pipe_size == '65(2.1/2")':
                    line.ms_pipe_weight_kg = 69.58

                elif line.ms_pipe_size == '80(3")':
                    line.ms_pipe_weight_kg = 92.96

                elif line.ms_pipe_size == '90(3.1/2")':
                    line.ms_pipe_weight_kg = 113.66

                elif line.ms_pipe_size == '100(4")':
                    line.ms_pipe_weight_kg = 136.15

                elif line.ms_pipe_size == '125(5")':
                    line.ms_pipe_weight_kg = 188.90

                elif line.ms_pipe_size == '150(6")':
                    line.ms_pipe_weight_kg = 259.63

                elif line.ms_pipe_size == '200(8")':
                    line.ms_pipe_weight_kg = 394.30

                elif line.ms_pipe_size == '250(10")':
                    line.ms_pipe_weight_kg = 585.44

                elif line.ms_pipe_size == '300(12")':
                    line.ms_pipe_weight_kg = 805.45

                else:
                    line.ms_pipe_weight_kg = False

            else:
                line.ms_pipe_weight_kg = False


    @api.depends('ms_pipe_size','ms_pipe_medium', 'thickness', 'product_id')
    def _compute_thickness(self):
        for line in self:
            if line.ms_pipe_size == '15(1/2")':

                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 2.65

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 2.77

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 3.73

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 4.78


            elif line.ms_pipe_size == '20(3/4")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 2.65

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 2.87

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 3.91

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 5.56

            elif line.ms_pipe_size == '25(1")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 3.25

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 3.38

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 4.55

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 6.35

            elif line.ms_pipe_size == '32(1/4")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 3.25

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 3.56

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 4.85

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 6.35

            elif line.ms_pipe_size == '40(1/2")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 3.25

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 3.68

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 5.08

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 7.14

            elif line.ms_pipe_size == '50(2")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 3.65

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 3.91

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 5.54

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 8.74


            elif line.ms_pipe_size == '65(2.1/2")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 3.65

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 5.16

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 7.01

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 9.53


            elif line.ms_pipe_size == '80(3")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 4.05

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 5.49

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 7.62

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 11.13

            elif line.ms_pipe_size == '90(3.1/2")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = False

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 5.74

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 8.08

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = False


            elif line.ms_pipe_size == '100(4")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 4.50

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 6.02

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 8.56

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 13.49


            elif line.ms_pipe_size == '125(5")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 5.00

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 6.55

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 9.52

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 15.88


            elif line.ms_pipe_size == '150(6")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 5.00

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 7.11

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 10.97

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 18.26

            elif line.ms_pipe_size == '200(8")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 6.35

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 8.18

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 12.7

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 23.08


            elif line.ms_pipe_size == '250(10")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 6.35

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 9.27

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 15.09

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 28.58


            elif line.ms_pipe_size == '300(12")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 6.35

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 10.31

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = 17.48

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 33.32


            elif line.ms_pipe_size == '350(14")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 6.35

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 11.13

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = False

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 33.32

            elif line.ms_pipe_size == '400(16")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 6.35

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 12.70

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = False

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 33.32


            elif line.ms_pipe_size == '450(18")':
                if line.ms_pipe_medium == 'pipe_medium_20':
                    line.thickness = 6.35

                elif line.ms_pipe_medium == 'black_pipe_40':
                    line.thickness = 14.27

                elif line.ms_pipe_medium == 'black_pipe_80':
                    line.thickness = False

                elif line.ms_pipe_medium == 'black_pipe_160':
                    line.thickness = 33.32

            else:
                line.thickness = False

    @api.depends('product_uom_qty', 'price_unit', 'ms_pipe_size', 'ms_pipe_medium', 'product_id')
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
    @api.depends('order_id.ms_pipe_line', 'sr_no', 'sr_no_char')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            value_sr = 1
            for line in order.ms_pipe_line:
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

