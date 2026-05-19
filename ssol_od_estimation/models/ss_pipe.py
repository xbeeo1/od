from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError
from collections import defaultdict


class SsPipe(models.Model):
    _name = "ss.pipe"
    _description = "SS pipe"
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

    ss_pipe_line = fields.One2many("ss.pipe.line", "order_id", string="")

    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')
    ], string="State", default='draft')

    def action_draft(self):
        self.state = "draft"

    def action_confirmed(self):
        self.state = "confirmed"

    def action_cancel(self):
        self.state = "cancel"


    @api.depends('total_amount', 'ss_pipe_line', 'ss_pipe_line.price_total')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.ss_pipe_line:
                total_amount += line.price_total

            rec.total_amount = total_amount

    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('Only cancelled record. You can Delete!'))
            if not rec.env.user.has_group('ssol_od_estimation.group_order_estimation_delete_access'):
                raise UserError(_('You can not delete this Maintenance Record. Contact your administrator.'))
            else:
                return super(SsPipe, self).unlink()


class SSPipeLine(models.Model):
    _name = 'ss.pipe.line'


    order_id = fields.Many2one('ss.pipe', string='Order Reference', required=True, ondelete='cascade')
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
    price_unit = fields.Monetary(string="Unit Price")
    price_subtotal = fields.Monetary(string="Subtotal", compute='_compute_price_subtotal')
    cost_price = fields.Monetary(string='Cost', currency_field='currency_id', compute='_compute_cost_margin')
    profit_margin = fields.Monetary(string='Margin', currency_field='currency_id', compute='_compute_cost_margin')
    tax_id = fields.Many2many('account.tax', string="Taxes", store=True, context={'active_test': False}, check_company=True)
    discount = fields.Monetary(string="Discount")
    disc_percentage = fields.Monetary(string="Disc%")
    amount_taxed = fields.Monetary(string="Tax Excl.", compute='_compute_amount_taxed')
    price_total = fields.Monetary(string="Tax Incl.", compute='_compute_amount_total')

    ss_pipe_size = fields.Selection(string="Nominal Pipe Size (ID)",
                                     selection=[('1/8"(10.290)', '1/8"__________(10.290)'),
                                                ('1/4"(13.720)','1/4"__________(13.720)'),
                                                ('3/8"(17.150)','3/8"__________(17.150)'),
                                                ('1/2"(21.340)','1/2"__________(21.340)'),
                                                ('3/4"(26.670)','3/4"__________(26.670)'),
                                                ('1.0"(33.400)','1.0"__________(33.400)'),
                                                ('1.1/4"(42.160)','1.1/4"__________(42.160)'),
                                                ('1.1/2"(48.260)','1.1/2"__________(48.260)'),
                                                ('2"(60.330)','2"__________(60.330)'),
                                                ('2.1/2"(73.030)', '2.1/2"__________(73.030)'),
                                                ('3"(88.900)', '3"__________(88.900)'),
                                                ('3.1/4"(101.600)', '3.1/4"__________(101.600)'),
                                                ('4"(114.330)', '4"__________(114.330)'),
                                                ('5"(141.300)', '5"__________(141.300)'),
                                                ('6"(168.280)', '6"__________(168.280)'),
                                                ('8"(219.080)', '8"__________(219.080)'),
                                                ('10"(273.050)', '10"__________(273.050)'),
                                                ('12"(323.850)', '12"__________(323.850)'),
                                                ], default='1/8"(10.290)')

    ss_pipe_schedule = fields.Selection(string="Pipe Schedule",
                                    selection=[('pipe_schedule_10', 'Schedule 10'),
                                               ('pipe_schedule_20', 'Schedule 20'),
                                               ('pipe_schedule_40', 'Schedule 40'),
                                               ('pipe_schedule_80', 'Schedule 80'),

                                               ], default='pipe_schedule_10')
    thickness = fields.Float(string="WT (mm)", compute='_compute_thickness_weight_kg_ft', digits=(16, 3))
    weight_kg_ft = fields.Float(string="Weight/ft (kg)", digits=(16, 3), compute='_compute_thickness_weight_kg_ft')
    pipe_kg_ft_qty = fields.Float(string="Pipe Qty", compute='_compute_qty',store=True)
    total_rft = fields.Float(string="Total Rft")
    total_weight = fields.Float(string="Total Weight (kg)", digits=(16, 2), compute='_compute_total_weight')

    @api.depends('total_rft', 'price_unit', 'ss_pipe_size', 'product_id','pipe_kg_ft_qty')
    def _compute_qty(self):
        for line in self:
            line.pipe_kg_ft_qty = line.total_rft / 20

    @api.depends('total_weight', 'weight_kg_ft', 'pipe_kg_ft_qty', 'ss_pipe_size', 'ss_pipe_schedule', 'product_id')
    def _compute_total_weight(self):
        for line in self:
            line.total_weight = line.pipe_kg_ft_qty * line.weight_kg_ft * 20

    @api.depends('ss_pipe_size', 'weight_kg_ft', 'ss_pipe_schedule', 'thickness', 'product_id')
    def _compute_thickness_weight_kg_ft(self):
        for line in self:
            if line.ss_pipe_size == '1/8"(10.290)':

                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 1.2
                    line.weight_kg_ft = 0.85

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 1.5
                    line.weight_kg_ft = 0.103

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 1.73
                    line.weight_kg_ft = 0.119

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 2.41
                    line.weight_kg_ft = 0.148


            elif line.ss_pipe_size == '1/4"(13.720)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 1.65
                    line.weight_kg_ft = 0.153

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 2.0
                    line.weight_kg_ft = 0.180

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 2.24
                    line.weight_kg_ft = 0.195

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 3.02
                    line.weight_kg_ft = 0.247

            elif line.ss_pipe_size == '3/8"(17.150)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 2.1
                    line.weight_kg_ft = 0.197

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 2.0
                    line.weight_kg_ft = 0.233

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 2.31
                    line.weight_kg_ft = 0.263

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 3.20
                    line.weight_kg_ft = 0.344

            elif line.ss_pipe_size == '1/2"(21.340)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 2.1
                    line.weight_kg_ft = 0.314

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 2.5
                    line.weight_kg_ft = 0.365

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 2.77
                    line.weight_kg_ft = 0.405

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 3.73
                    line.weight_kg_ft = 0.504

            elif line.ss_pipe_size == '3/4"(26.670)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 2.8
                    line.weight_kg_ft = 0.402

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 2.5
                    line.weight_kg_ft = 0.472

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 2.887
                    line.weight_kg_ft = 0.539

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 3.91
                    line.weight_kg_ft = 0.695

            elif line.ss_pipe_size == '1.0"(33.400)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 2.8
                    line.weight_kg_ft = 0.667

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 3.00
                    line.weight_kg_ft = 0.710

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 3.38
                    line.weight_kg_ft = 0.795

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 4.55
                    line.weight_kg_ft = 1.015


            elif line.ss_pipe_size == '1.1/4"(42.160)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 2.8
                    line.weight_kg_ft = 0.553

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 3.0
                    line.weight_kg_ft = 0.911

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 3.56
                    line.weight_kg_ft = 1.076

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 4.85
                    line.weight_kg_ft = 1.414


            elif line.ss_pipe_size == '1.1/2"(48.260)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 2.8
                    line.weight_kg_ft = 0.978

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 3.0
                    line.weight_kg_ft = 1.045

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 3.68
                    line.weight_kg_ft = 1.268

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 5.08
                    line.weight_kg_ft = 1.695


            elif line.ss_pipe_size == '2"(60.330)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 2.8
                    line.weight_kg_ft = 1.239

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 3.5
                    line.weight_kg_ft = 1.529

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 3.91
                    line.weight_kg_ft = 1.685

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 5.54
                    line.weight_kg_ft = 2.310


            elif line.ss_pipe_size == '2.1/2"(73.030)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 3.00
                    line.weight_kg_ft = 1.680

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 3.5
                    line.weight_kg_ft = 1.950

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 5.16
                    line.weight_kg_ft = 2.826

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 7.01
                    line.weight_kg_ft = 3.719


            elif line.ss_pipe_size == '3"(88.900)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 3.05
                    line.weight_kg_ft = 1.975

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 4.0
                    line.weight_kg_ft = 2.600

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 5.49
                    line.weight_kg_ft = 3.506

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 7.62
                    line.weight_kg_ft = 4.725


            elif line.ss_pipe_size == '3.1/4"(101.600)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 3.05
                    line.weight_kg_ft = 2.262

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 4.0
                    line.weight_kg_ft = 2.980

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 5.79
                    line.weight_kg_ft = 4.176

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 8.08
                    line.weight_kg_ft = 5.792


            elif line.ss_pipe_size == '4"(114.330)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 3.05
                    line.weight_kg_ft = 2.550

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 4.0
                    line.weight_kg_ft = 3.334

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 6.02
                    line.weight_kg_ft = 5.210

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 8.56
                    line.weight_kg_ft = 7.241


            elif line.ss_pipe_size == '5"(141.300)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 3.40
                    line.weight_kg_ft = 3.535

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 5.0
                    line.weight_kg_ft = 5.152

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 6.55
                    line.weight_kg_ft = 8.567

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 9.52
                    line.weight_kg_ft = 9.451


            elif line.ss_pipe_size == '6"(168.280)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 3.40
                    line.weight_kg_ft = 4.207

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 5.0
                    line.weight_kg_ft = 6.128

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 7.11
                    line.weight_kg_ft = 8.567

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 10.97
                    line.weight_kg_ft = 12.957


            elif line.ss_pipe_size == '8"(219.080)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 3.76
                    line.weight_kg_ft = 6.500

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 6.5
                    line.weight_kg_ft = 10.426

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 8.18
                    line.weight_kg_ft = 13.048

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 13.048
                    line.weight_kg_ft = 19.756


            elif line.ss_pipe_size == '10"(273.050)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 4.19
                    line.weight_kg_ft = 8.048

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 6.5
                    line.weight_kg_ft = 12.957

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 9.27
                    line.weight_kg_ft = 18.353

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 12.70
                    line.weight_kg_ft = 29.115


            elif line.ss_pipe_size == '12"(323.850)':
                if line.ss_pipe_schedule == 'pipe_schedule_10':
                    line.thickness = 4.57
                    line.weight_kg_ft = 10.800

                elif line.ss_pipe_schedule == 'pipe_schedule_20':
                    line.thickness = 6.5
                    line.weight_kg_ft = 15.881

                elif line.ss_pipe_schedule == 'pipe_schedule_40':
                    line.thickness = 9.52
                    line.weight_kg_ft = 29.268

                elif line.ss_pipe_schedule == 'pipe_schedule_80':
                    line.thickness = 12.70
                    line.weight_kg_ft = 39.939

            else:
                line.thickness = False
                line.weight_kg_ft = False


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
    @api.depends('order_id.ss_pipe_line', 'sr_no', 'sr_no_char')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            value_sr = 1
            for line in order.ss_pipe_line:
                value_sr += 1

    @api.depends('product_id', 'price_unit', 'price_subtotal', 'total_weight')
    def _compute_price_subtotal(self):
        for line in self:
            subtotal = line.price_unit * line.total_rft
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

