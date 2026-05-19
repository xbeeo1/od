from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError
import math


class CopperTube(models.Model):
    _name = "copper.tube"
    _description = "Copper Tube"
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
    copper_tube_type = fields.Selection(string="Copper Tube type", selection=[('pancake', 'Pancake'), ('lwc', 'Lwc')], default='pancake')

    active = fields.Boolean(string="Active", default=True)
    image_1920 = fields.Binary(string='Image')

    copper_pancake_line = fields.One2many("copper.pancake.line", "order_id", string="")
    copper_lwc_line = fields.One2many("copper.lwc.line", "order_id", string="")

    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')
    ], string="State", default='draft')

    def action_draft(self):
        self.state = "draft"

    def action_confirmed(self):
        self.state = "confirmed"

    def action_cancel(self):
        self.state = "cancel"


    @api.depends('total_amount', 'copper_pancake_line', 'copper_pancake_line.price_total')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.copper_pancake_line:
                total_amount += line.price_total

            rec.total_amount = total_amount

    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('Only cancelled record. You can Delete!'))
            if not rec.env.user.has_group('ssol_od_estimation.group_order_estimation_delete_access'):
                raise UserError(_('You can not delete this Maintenance Record. Contact your administrator.'))
            else:
                return super(CopperTube, self).unlink()





class CopperPancakeLine(models.Model):
    _name = 'copper.pancake.line'


    order_id = fields.Many2one('copper.tube', string='Order Reference', required=True, ondelete='cascade')
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



    pancake_inches = fields.Selection(string='"',
                                     selection=[('3/16', '3/16"'),
                                                ('1/4', '1/4"'),('5/16', '5/16"'),
                                                ('3/8', '3/8"'),('1/2', '1/2"'),
                                                ('5/8', '5/8"'),('3/4', '3/4"'),
                                                ], default='3/16')
    pancake_mm = fields.Float(string="⌀", compute='_compute_pancake_mm')


    swg = fields.Selection(string="SWG",
                                      selection=[('16', '16'),
                                                 ('16', '16'),('17', '17'),
                                                 ('18', '18'),('19', '19'),
                                                 ('20', '20'),('21', '21'),
                                                 ('22', '22'),('23', '23'),
                                                 ('24', '24'),('25', '25'),
                                                 ('26', '26'),('27', '27'),
                                                 ('28', '28')

                                            ], default='16')  # fetch data from copper tubes
    thickness = fields.Float(string="W.TH (mm)", compute='_compute_copper_weight')


    gage_size = fields.Selection(string="Gage/Size",
                                 selection=[('10', '10'),
                                            ('12', '12'), ('14', '14'),
                                            ('15', '15'), ('16', '16'),
                                            ('17', '17'), ('18', '18'),
                                            ('19', '19'), ('20', '20'),
                                            ('21', '21'), ('22', '22'),
                                            ('23', '23'), ('24', '24'),
                                            ('25', '25'), ('26', '26'),
                                            ('21', '21'),
                                            ], default='10')  # fetch data from copper tubes

    copper_weight = fields.Float(string="weight/coil", compute='_compute_copper_weight')
    length_inches = fields.Float(string="Length(Inches)")
    total_copper = fields.Float(string="No. of Tubes / Coil", compute='_compute_total_copper')
    total_coil_required = fields.Float(string="No. of Coil Required", compute='_compute_total_coil_required')
    total_weight = fields.Float(string="Total Weight", digits=(16, 2), compute='_compute_total_weight')


    @api.depends('pancake_inches', 'pancake_mm', 'product_id')
    def _compute_pancake_mm(self):
        for line in self:
            if line.pancake_inches == '3/16':
                line.pancake_mm = 4.76

            elif line.pancake_inches == '1/4':
                line.pancake_mm = 6.35

            elif line.pancake_inches == '5/16':
                line.pancake_mm = 7.94

            elif line.pancake_inches == '3/8':
                line.pancake_mm = 9.52

            elif line.pancake_inches == '1/2':
                line.pancake_mm = 12.7

            elif line.pancake_inches == '5/8':
                line.pancake_mm = 15.88

            elif line.pancake_inches == '3/4':
                line.pancake_mm = 19.05
            else:
                line.pancake_mm = False


    @api.depends('pancake_inches', 'swg', 'thickness', 'copper_weight', 'product_id')
    def _compute_copper_weight(self):
        for line in self:

            if line.swg == '16':
                line.thickness = 1.66

                if line.pancake_inches == '3/16':
                    line.copper_weight = False

                elif line.pancake_inches == '1/4':
                    line.copper_weight = False

                elif line.pancake_inches == '5/16':
                    line.copper_weight = False

                elif line.pancake_inches == '3/8':
                    line.copper_weight = False

                elif line.pancake_inches == '1/2':
                    line.copper_weight = False

                elif line.pancake_inches == '5/8':
                    line.copper_weight = False

                elif line.pancake_inches == '3/4':
                    line.copper_weight = False
                else:
                    line.copper_weight = False



            elif line.swg == '17':
                line.thickness = 1.42
                if line.pancake_inches == '3/16':
                    line.copper_weight = False

                elif line.pancake_inches == '1/4':
                    line.copper_weight = False

                elif line.pancake_inches == '5/16':
                    line.copper_weight = False

                elif line.pancake_inches == '3/8':
                    line.copper_weight = False

                elif line.pancake_inches == '1/2':
                    line.copper_weight = False

                elif line.pancake_inches == '5/8':
                    line.copper_weight = False

                elif line.pancake_inches == '3/4':
                    line.copper_weight = False

                else:
                    line.copper_weight = False


            elif line.swg == '18':
                line.thickness = 1.22
                if line.pancake_inches == '3/16':
                    line.copper_weight = False

                elif line.pancake_inches == '1/4':
                    line.copper_weight = False

                elif line.pancake_inches == '5/16':
                    line.copper_weight = False

                elif line.pancake_inches == '3/8':
                    line.copper_weight = 4.25

                elif line.pancake_inches == '1/2':
                    line.copper_weight = 5.88

                elif line.pancake_inches == '5/8':
                    line.copper_weight = 7.51

                elif line.pancake_inches == '3/4':
                    line.copper_weight = 9.14
                else:
                    line.copper_weight = False


            elif line.swg == '19':
                line.thickness = 1.02
                if line.pancake_inches == '3/16':
                    line.copper_weight = False

                elif line.pancake_inches == '1/4':
                    line.copper_weight = False

                elif line.pancake_inches == '5/16':
                    line.copper_weight = False

                elif line.pancake_inches == '3/8':
                    line.copper_weight = False

                elif line.pancake_inches == '1/2':
                    line.copper_weight = False

                elif line.pancake_inches == '5/8':
                    line.copper_weight = False

                elif line.pancake_inches == '3/4':
                    line.copper_weight = False
                else:
                    line.copper_weight = False


            elif line.swg == '20':
                line.thickness = 0.91
                if line.pancake_inches == '3/16':
                    line.copper_weight = False

                elif line.pancake_inches == '1/4':
                    line.copper_weight = 2.08

                elif line.pancake_inches == '5/16':
                    line.copper_weight = 2.69

                elif line.pancake_inches == '3/8':
                    line.copper_weight = 3.29

                elif line.pancake_inches == '1/2':
                    line.copper_weight = 4.51

                elif line.pancake_inches == '5/8':
                    line.copper_weight = 5.72

                elif line.pancake_inches == '3/4':
                    line.copper_weight = 6.93
                else:
                    line.copper_weight = False


            elif line.swg == '21':
                line.thickness = 0.81
                if line.pancake_inches == '3/16':
                    line.copper_weight = False

                elif line.pancake_inches == '1/4':
                    line.copper_weight = 1.88

                elif line.pancake_inches == '5/16':
                    line.copper_weight = 2.43

                elif line.pancake_inches == '3/8':
                    line.copper_weight = 2.96

                elif line.pancake_inches == '1/2':
                    line.copper_weight = 4.04

                elif line.pancake_inches == '5/8':
                    line.copper_weight = 5.13

                elif line.pancake_inches == '3/4':
                    line.copper_weight = 6.21
                else:
                    line.copper_weight = False


            elif line.swg == '22':
                line.thickness = 0.71
                if line.pancake_inches == '3/16':
                    line.copper_weight = False

                elif line.pancake_inches == '1/4':
                    line.copper_weight = 1.68

                elif line.pancake_inches == '5/16':
                    line.copper_weight = 2.16

                elif line.pancake_inches == '3/8':
                    line.copper_weight = 2.63

                elif line.pancake_inches == '1/2':
                    line.copper_weight = 3.58

                elif line.pancake_inches == '5/8':
                    line.copper_weight = 4.52

                elif line.pancake_inches == '3/4':
                    line.copper_weight = 5.47
                else:
                    line.copper_weight = False


            elif line.swg == '23':
                line.thickness = 0.61
                if line.pancake_inches == '3/16':
                    line.copper_weight = 1.06

                elif line.pancake_inches == '1/4':
                    line.copper_weight = 1.47

                elif line.pancake_inches == '5/16':
                    line.copper_weight = 1.88

                elif line.pancake_inches == '3/8':
                    line.copper_weight = 2.28

                elif line.pancake_inches == '1/2':
                    line.copper_weight = 3.10

                elif line.pancake_inches == '5/8':
                    line.copper_weight = 3.91

                elif line.pancake_inches == '3/4':
                    line.copper_weight = 4.72
                else:
                    line.copper_weight = False


            elif line.swg == '24':
                line.thickness = 0.56
                if line.pancake_inches == '3/16':
                    line.copper_weight = 0.99

                elif line.pancake_inches == '1/4':
                    line.copper_weight = 1.36

                elif line.pancake_inches == '5/16':
                    line.copper_weight = 1.74

                elif line.pancake_inches == '3/8':
                    line.copper_weight = 2.11

                elif line.pancake_inches == '1/2':
                    line.copper_weight = 2.86

                elif line.pancake_inches == '5/8':
                    line.copper_weight = 3.60

                elif line.pancake_inches == '3/4':
                    line.copper_weight = False
                else:
                    line.copper_weight = False


            elif line.swg == '25':
                line.thickness = 0.51
                if line.pancake_inches == '3/16':
                    line.copper_weight = 0.91

                elif line.pancake_inches == '1/4':
                    line.copper_weight = 1.25

                elif line.pancake_inches == '5/16':
                    line.copper_weight = 1.59

                elif line.pancake_inches == '3/8':
                    line.copper_weight = 1.93

                elif line.pancake_inches == '1/2':
                    line.copper_weight = 2.61

                elif line.pancake_inches == '5/8':
                    line.copper_weight = False

                elif line.pancake_inches == '3/4':
                    line.copper_weight = False
                else:
                    line.copper_weight = False


            elif line.swg == '26':
                line.thickness = 0.46
                if line.pancake_inches == '3/16':
                    line.copper_weight = False

                elif line.pancake_inches == '1/4':
                    line.copper_weight = False

                elif line.pancake_inches == '5/16':
                    line.copper_weight = False

                elif line.pancake_inches == '3/8':
                    line.copper_weight = False

                elif line.pancake_inches == '1/2':
                    line.copper_weight = False

                elif line.pancake_inches == '5/8':
                    line.copper_weight = False

                elif line.pancake_inches == '3/4':
                    line.copper_weight = False

                else:
                    line.copper_weight = False

            elif line.swg == '27':
                line.thickness = 0.42
                if line.pancake_inches == '3/16':
                    line.copper_weight = False

                elif line.pancake_inches == '1/4':
                    line.copper_weight = 2

                elif line.pancake_inches == '5/16':
                    line.copper_weight = False

                elif line.pancake_inches == '3/8':
                    line.copper_weight = 2

                elif line.pancake_inches == '1/2':
                    line.copper_weight = False

                elif line.pancake_inches == '5/8':
                    line.copper_weight = False

                elif line.pancake_inches == '3/4':
                    line.copper_weight = False

                else:
                    line.copper_weight = False

            elif line.swg == '28':
                line.thickness = 1.02
                if line.pancake_inches == '3/16':
                    line.copper_weight = False

                elif line.pancake_inches == '1/4':
                    line.copper_weight = False

                elif line.pancake_inches == '5/16':
                    line.copper_weight = False

                elif line.pancake_inches == '3/8':
                    line.copper_weight = False

                elif line.pancake_inches == '1/2':
                    line.copper_weight = False

                elif line.pancake_inches == '5/8':
                    line.copper_weight = False

                elif line.pancake_inches == '3/4':
                    line.copper_weight = False
                else:
                    line.copper_weight = False

            else:
                line.thickness = False
                line.copper_weight = False



    @api.depends('total_copper', 'length_inches', 'product_id')
    def _compute_total_copper(self):
        for line in self:
            if line.length_inches:
                line.total_copper = 600/line.length_inches
            else:
                line.total_copper = False



    @api.depends('total_copper', 'length_inches', 'product_uom_qty', 'product_id')
    def _compute_total_coil_required(self):
        for line in self:
            if line.total_copper:
                total_coil = line.product_uom_qty / line.total_copper
                # Round up to the next integer if there is a fractional part
                line.total_coil_required = math.ceil(total_coil)
            else:
                line.total_coil_required = False


    @api.depends('total_weight', 'copper_weight', 'gage_size', 'swg', 'product_uom_qty','total_coil_required', 'product_id')
    def _compute_total_weight(self):
        for line in self:
            if line.total_coil_required:
                line.total_weight = line.total_coil_required * line.copper_weight
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
    @api.depends('order_id.copper_pancake_line', 'sr_no', 'sr_no_char')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            value_sr = 1
            for line in order.copper_pancake_line:
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




class CopperLwcLine(models.Model):
    _name = 'copper.lwc.line'


    order_id = fields.Many2one('copper.tube', string='Order Reference', required=True, ondelete='cascade')
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
    price_unit = fields.Monetary(string="Price / Kg")
    price_subtotal = fields.Monetary(string="Subtotal", compute='_compute_price_subtotal')
    cost_price = fields.Monetary(string='Cost', currency_field='currency_id', compute='_compute_cost_margin')
    profit_margin = fields.Monetary(string='Margin', currency_field='currency_id', compute='_compute_cost_margin')
    tax_id = fields.Many2many('account.tax', string="Taxes", store=True, context={'active_test': False}, check_company=True)
    discount = fields.Monetary(string="Discount")
    disc_percentage = fields.Monetary(string="Disc%")
    amount_taxed = fields.Monetary(string="Tax Excl.", compute='_compute_amount_taxed')
    price_total = fields.Monetary(string="Tax Incl.", compute='_compute_amount_total')



    lwc_inches = fields.Selection(string="Inches",
                                     selection=[('3/16', '3/16'),
                                                ('1/4', '1/4'),('5/16', '5/16'),
                                                ('3/8', '3/8'),('1/2', '1/2'),
                                                ('5/8', '5/8'),('3/4', '3/4'),
                                                ], default='3/16')
    lwc_mm = fields.Float(string="MM", compute='_compute_lwc_mm')


    swg = fields.Selection(string="SWG",
                                      selection=[('16', '16'),
                                                 ('16', '16'),('17', '17'),
                                                 ('18', '18'),('19', '19'),
                                                 ('20', '20'),('21', '21'),
                                                 ('22', '22'),('23', '23'),
                                                 ('24', '24'),('25', '25'),
                                                 ('26', '26'),('27', '27'),
                                                 ('28', '28')

                                            ], default='16')  # fetch data from copper tubes
    thickness = fields.Float(string="W.T", compute='_compute_copper_weight')


    gage_size = fields.Selection(string="Gage/Size",
                                 selection=[('10', '10'),
                                            ('12', '12'), ('14', '14'),
                                            ('15', '15'), ('16', '16'),
                                            ('17', '17'), ('18', '18'),
                                            ('19', '19'), ('20', '20'),
                                            ('21', '21'), ('22', '22'),
                                            ('23', '23'), ('24', '24'),
                                            ('25', '25'), ('26', '26'),
                                            ('21', '21'),
                                            ], default='10')  # fetch data from copper tubes

    copper_weight = fields.Float(string="Weight of one Coil", compute='_compute_copper_weight')
    length_inches = fields.Float(string="Length(Inches)")
    total_copper = fields.Float(string="No. of Tube from one Coil", compute='_compute_total_copper')
    total_coil_required = fields.Float(string="No. of Coil Required", compute='_compute_total_coil_required')
    total_weight = fields.Float(string="Total Weight", digits=(16, 4), compute='_compute_total_weight')


    @api.depends('lwc_inches', 'lwc_mm', 'product_id')
    def _compute_lwc_mm(self):
        for line in self:
            if line.lwc_inches == '3/16':
                line.lwc_mm = 4.76

            elif line.lwc_inches == '1/4':
                line.lwc_mm = 6.35

            elif line.lwc_inches == '5/16':
                line.lwc_mm = 7.94

            elif line.lwc_inches == '3/8':
                line.lwc_mm = 9.52

            elif line.lwc_inches == '1/2':
                line.lwc_mm = 12.7

            elif line.lwc_inches == '5/8':
                line.lwc_mm = 15.88

            elif line.lwclwc_inches == '3/4':
                line.lwc_mm = 19.05
            else:
                line.lwc_mm = False


    @api.depends('lwc_inches', 'swg', 'thickness', 'copper_weight', 'product_id')
    def _compute_copper_weight(self):
        for line in self:

            if line.swg == '16':
                line.thickness = 1.66

                if line.lwc_inches == '3/16':
                    line.copper_weight = False

                elif line.lwc_inches == '1/4':
                    line.copper_weight = False

                elif line.lwc_inches == '5/16':
                    line.copper_weight = False

                elif line.lwc_inches == '3/8':
                    line.copper_weight = False

                elif line.lwc_inches == '1/2':
                    line.copper_weight = False

                elif line.lwc_inches == '5/8':
                    line.copper_weight = False

                elif line.lwc_inches == '3/4':
                    line.copper_weight = False
                else:
                    line.copper_weight = False



            elif line.swg == '17':
                line.thickness = 1.42
                if line.lwc_inches == '3/16':
                    line.copper_weight = False

                elif line.lwc_inches == '1/4':
                    line.copper_weight = False

                elif line.lwc_inches == '5/16':
                    line.copper_weight = False

                elif line.lwc_inches == '3/8':
                    line.copper_weight = False

                elif line.lwc_inches == '1/2':
                    line.copper_weight = False

                elif line.lwc_inches == '5/8':
                    line.copper_weight = False

                elif line.lwc_inches == '3/4':
                    line.copper_weight = False

                else:
                    line.copper_weight = False


            elif line.swg == '18':
                line.thickness = 1.22
                if line.lwc_inches == '3/16':
                    line.copper_weight = False

                elif line.lwc_inches == '1/4':
                    line.copper_weight = False

                elif line.lwc_inches == '5/16':
                    line.copper_weight = False

                elif line.lwc_inches == '3/8':
                    line.copper_weight = 4.25

                elif line.lwc_inches == '1/2':
                    line.copper_weight = 5.88

                elif line.lwc_inches == '5/8':
                    line.copper_weight = 7.51

                elif line.lwc_inches == '3/4':
                    line.copper_weight = 9.14
                else:
                    line.copper_weight = False


            elif line.swg == '19':
                line.thickness = 1.02
                if line.lwc_inches == '3/16':
                    line.copper_weight = False

                elif line.lwc_inches == '1/4':
                    line.copper_weight = False

                elif line.lwc_inches == '5/16':
                    line.copper_weight = False

                elif line.lwc_inches == '3/8':
                    line.copper_weight = False

                elif line.lwc_inches == '1/2':
                    line.copper_weight = False

                elif line.lwc_inches == '5/8':
                    line.copper_weight = False

                elif line.lwc_inches == '3/4':
                    line.copper_weight = False
                else:
                    line.copper_weight = False


            elif line.swg == '20':
                line.thickness = 0.91
                if line.lwc_inches == '3/16':
                    line.copper_weight = False

                elif line.lwc_inches == '1/4':
                    line.copper_weight = 2.08

                elif line.lwc_inches == '5/16':
                    line.copper_weight = 2.69

                elif line.lwc_inches == '3/8':
                    line.copper_weight = 3.29

                elif line.lwc_inches == '1/2':
                    line.copper_weight = 4.51

                elif line.lwc_inches == '5/8':
                    line.copper_weight = 5.72

                elif line.lwc_inches == '3/4':
                    line.copper_weight = 6.93
                else:
                    line.copper_weight = False


            elif line.swg == '21':
                line.thickness = 0.81
                if line.lwc_inches == '3/16':
                    line.copper_weight = False

                elif line.lwc_inches == '1/4':
                    line.copper_weight = 1.88

                elif line.lwc_inches == '5/16':
                    line.copper_weight = 2.43

                elif line.lwc_inches == '3/8':
                    line.copper_weight = 2.69

                elif line.lwc_inches == '1/2':
                    line.copper_weight = 4.04

                elif line.lwc_inches == '5/8':
                    line.copper_weight = 5.13

                elif line.lwc_inches == '3/4':
                    line.copper_weight = 6.21
                else:
                    line.copper_weight = False


            elif line.swg == '22':
                line.thickness = 0.71
                if line.lwc_inches == '3/16':
                    line.copper_weight = False

                elif line.lwc_inches == '1/4':
                    line.copper_weight = 1.68

                elif line.lwc_inches == '5/16':
                    line.copper_weight = 2.16

                elif line.lwc_inches == '3/8':
                    line.copper_weight = 2.63

                elif line.lwc_inches == '1/2':
                    line.copper_weight = 3.58

                elif line.lwc_inches == '5/8':
                    line.copper_weight = 4.52

                elif line.lwc_inches == '3/4':
                    line.copper_weight = 5.47
                else:
                    line.copper_weight = False


            elif line.swg == '23':
                line.thickness = 0.61
                if line.lwc_inches == '3/16':
                    line.copper_weight = 1.06

                elif line.lwc_inches == '1/4':
                    line.copper_weight = 1.47

                elif line.lwc_inches == '5/16':
                    line.copper_weight = 1.88

                elif line.lwc_inches == '3/8':
                    line.copper_weight = 2.28

                elif line.lwc_inches == '1/2':
                    line.copper_weight = 3.10

                elif line.lwc_inches == '5/8':
                    line.copper_weight = 3.91

                elif line.lwc_inches == '3/4':
                    line.copper_weight = 4.72
                else:
                    line.copper_weight = False


            elif line.swg == '24':
                line.thickness = 0.56
                if line.lwc_inches == '3/16':
                    line.copper_weight = 0.99

                elif line.lwc_inches == '1/4':
                    line.copper_weight = 1.36

                elif line.lwc_inches == '5/16':
                    line.copper_weight = 1.74

                elif line.lwc_inches == '3/8':
                    line.copper_weight = 2.11

                elif line.lwc_inches == '1/2':
                    line.copper_weight = 2.86

                elif line.lwc_inches == '5/8':
                    line.copper_weight = 3.60

                elif line.lwc_inches == '3/4':
                    line.copper_weight = False
                else:
                    line.copper_weight = False


            elif line.swg == '25':
                line.thickness = 0.51
                if line.lwc_inches == '3/16':
                    line.copper_weight = 0.91

                elif line.lwc_inches == '1/4':
                    line.copper_weight = 1.25

                elif line.lwc_inches == '5/16':
                    line.copper_weight = 1.59

                elif line.lwc_inches == '3/8':
                    line.copper_weight = 1.93

                elif line.lwc_inches == '1/2':
                    line.copper_weight = 2.61

                elif line.lwc_inches == '5/8':
                    line.copper_weight = False

                elif line.lwc_inches == '3/4':
                    line.copper_weight = False
                else:
                    line.copper_weight = False


            elif line.swg == '26':
                line.thickness = 0.46
                if line.lwc_inches == '3/16':
                    line.copper_weight = False

                elif line.lwc_inches == '1/4':
                    line.copper_weight = False

                elif line.lwc_inches == '5/16':
                    line.copper_weight = False

                elif line.lwc_inches == '3/8':
                    line.copper_weight = False

                elif line.lwc_inches == '1/2':
                    line.copper_weight = False

                elif line.lwc_inches == '5/8':
                    line.copper_weight = False

                elif line.lwc_inches == '3/4':
                    line.copper_weight = False

                else:
                    line.copper_weight = False

            elif line.swg == '27':
                line.thickness = 0.42
                if line.lwc_inches == '3/16':
                    line.copper_weight = False

                elif line.lwc_inches == '1/4':
                    line.copper_weight = 2

                elif line.lwc_inches == '5/16':
                    line.copper_weight = False

                elif line.lwc_inches == '3/8':
                    line.copper_weight = 2

                elif line.lwc_inches == '1/2':
                    line.copper_weight = False

                elif line.lwc_inches == '5/8':
                    line.copper_weight = False

                elif line.lwc_inches == '3/4':
                    line.copper_weight = False

                else:
                    line.copper_weight = False

            elif line.swg == '28':
                line.thickness = 1.02
                if line.lwc_inches == '3/16':
                    line.copper_weight = False

                elif line.lwc_inches == '1/4':
                    line.copper_weight = False

                elif line.lwc_inches == '5/16':
                    line.copper_weight = False

                elif line.lwc_inches == '3/8':
                    line.copper_weight = False

                elif line.lwc_inches == '1/2':
                    line.copper_weight = False

                elif line.lwc_inches == '5/8':
                    line.copper_weight = False

                elif line.lwc_inches == '3/4':
                    line.copper_weight = False
                else:
                    line.copper_weight = False

            else:
                line.thickness = False
                line.copper_weight = False



    @api.depends('total_copper', 'length_inches', 'product_id')
    def _compute_total_copper(self):
        for line in self:
            if line.length_inches:
                line.total_copper = 600/line.length_inches
            else:
                line.total_copper = False



    @api.depends('total_copper', 'length_inches', 'product_uom_qty', 'product_id')
    def _compute_total_coil_required(self):
        for line in self:
            if line.total_copper:
                total_coil = line.product_uom_qty / line.total_copper
                # Round up to the next integer if there is a fractional part
                line.total_coil_required = math.ceil(total_coil)
            else:
                line.total_coil_required = False


    @api.depends('total_weight', 'copper_weight', 'gage_size', 'swg', 'product_uom_qty','total_coil_required', 'product_id')
    def _compute_total_weight(self):
        for line in self:
            if line.total_coil_required:
                line.total_weight = line.total_coil_required * line.copper_weight
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
    @api.depends('order_id.copper_lwc_line', 'sr_no', 'sr_no_char')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            value_sr = 1
            for line in order.copper_lwc_line:
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







class CopperLwcLine(models.Model):
    _name = 'copper.tube.line'