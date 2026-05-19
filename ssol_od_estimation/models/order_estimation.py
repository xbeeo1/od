from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError
from collections import defaultdict


class OrderEstimation(models.Model):
    _name = "order.estimation"
    _description = "Order Estimation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    sequence = fields.Char(string='Sequence', required=True, copy=False, readonly=True,
                           default=lambda self: _('New Order'))
    name = fields.Char(string='Name', tracking=True, compute='_compute_name')
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True, required=True)
    product_tmpl_id = fields.Many2one('product.template', string='product', tracking=True, required=True)
    product_qty = fields.Float(string="Quantity", tracking=True)
    total_amount = fields.Float(string="Total Amount", tracking=True, compute='_compute_total_amount')
    order_date = fields.Date("Date", tracking=True, default=date.today())
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self:self.env.user.id, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self:self.env.company.id, readonly=True)
    attachment = fields.Binary(string="Attachment", tracking=True)
    description = fields.Text(string="Note", tracking=True)

    # INVISIBLE FIELDS
    compute_lines_total = fields.Boolean(string="Compute Lines Total", compute='_compute_amount_lines_total')
    is_mo = fields.Boolean(string="Is Mo")
    bom_id = fields.Many2one("mrp.bom", string="Bill of Material", tracking=True)
    mrp_order = fields.Many2one("mrp.production", string="MO Order", tracking=True)

    active = fields.Boolean(string="Active", default=True)
    image_1920 = fields.Binary(string='Image')

    state = fields.Selection([
        ('draft', 'Draft'), ('in_progress', 'In-Progress'),
        ('confirmed', 'Confirmed'), ('cancel', 'Cancelled')
    ], string="State", default='draft')

    order_estimation_line = fields.One2many("order.estimation.line", "order_id", string="")

    # @api.depends('order_estimation_line')
    def action_compute_estimation(self):
        for rec in self:
            data = []

            # Prepare GI Order Data
            data.extend(rec.prepare_order_line_data('gi.order', 'gi_order_line', rec.id))

            # Prepare MS Channel Order Data
            data.extend(rec.prepare_order_line_data('ms.channel', 'ms_channel_line', rec.id))

            # Prepare MS Flat Order Data
            data.extend(rec.prepare_order_line_data('ms.flat', 'ms_flat_line', rec.id))

            # Prepare MS Flat Order Data
            data.extend(rec.prepare_order_line_data('ms.angle', 'ms_angle_line', rec.id))

            # Prepare MS Sheet Order Data
            data.extend(rec.prepare_order_line_data('ms.sheet', 'ms_sheet_line', rec.id))

            # Prepare MS Sheet Order Data
            data.extend(rec.prepare_order_line_data('ms.plate', 'ms_plate_line', rec.id))

            # Prepare MS square Order Data
            data.extend(rec.prepare_order_line_data('ms.square', 'ms_square_line', rec.id))

            # Prepare MS square Order Data
            data.extend(rec.prepare_order_line_data('ms.round', 'ms_round_line', rec.id))


            """MS PIPE DATA NEED TO SHOW"""
            data.extend(rec.prepare_order_line_data('ms.pipe', 'ms_pipe_line', rec.id))

            # Prepare MS Tube Order Data
            data.extend(rec.prepare_order_line_data('ms.tube', 'ms_tube_line', rec.id))


            # Prepare SS Flat Stripes Order Data
            data.extend(rec.prepare_order_line_data('ss.flats', 'ss_flats_line', rec.id))

            # Prepare SS angles Order Data
            data.extend(rec.prepare_order_line_data('ss.angles', 'ss_angles_line', rec.id))

            # Prepare SS rods Order Data
            data.extend(rec.prepare_order_line_data('ss.rods', 'ss_rods_line', rec.id))

            # Prepare SS sheets Order Data
            data.extend(rec.prepare_order_line_data('ss.sheets', 'ss_sheets_line', rec.id))

            # Prepare SS pipe Order Data
            data.extend(rec.prepare_order_line_data('ss.pipe', 'ss_pipe_line', rec.id))

            # Prepare Copper Tube Order Data
            data.extend(rec.prepare_order_line_data('copper.tube', 'copper_pancake_line', rec.id))

            # Prepare Copper Sheet Order Data
            data.extend(rec.prepare_order_line_data('copper.sheet', 'copper_sheet_line', rec.id))

            # Prepare Aluminum Sheet Order Data
            data.extend(rec.prepare_order_line_data('aluminum.sheet', 'aluminum_sheet_line', rec.id))

            # Prepare Finished Goods Order Data
            data.extend(rec.prepare_order_line_data('finished.goods', 'finished_goods_line', rec.id))


            rec.order_estimation_line = False
            rec.order_estimation_line = data



    def prepare_order_line_data(self, model_name, line_attr, parent_order_id):
        """Helper function to prepare order line data from specified model and line attribute."""
        # print('model_name..............', model_name)
        order_lines = []
        order = self.env[model_name].search([('parent_order_id', '=', parent_order_id), ('state', '=', 'confirmed')])
        if order:
            if model_name == 'ms.pipe' or model_name == 'ms.tube':
                for line in getattr(order, line_attr):
                    order_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_uom_qty': line.product_uom_qty,
                        # 'price_unit': line.price_unit * 20,
                        'price_unit': line.rate_per_rft * 20,
                        'cost_price': line.cost_price,
                        'profit_margin': line.profit_margin,
                        'price_subtotal': line.price_subtotal,
                        'tax_id': [(4, tax.id) for tax in line.tax_id],
                        'discount': line.discount,
                        'disc_percentage': line.disc_percentage,
                        'amount_taxed': line.amount_taxed,
                        'price_total': line.price_total,
                    }))

            elif model_name == 'finished.goods':
                for line in getattr(order, line_attr):
                    order_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_uom_qty': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'cost_price': line.cost_price,
                        'profit_margin': line.profit_margin,
                        'price_subtotal': line.price_subtotal,
                        'tax_id': [(4, tax.id) for tax in line.tax_id],
                        'discount': line.discount,
                        'disc_percentage': line.disc_percentage,
                        'amount_taxed': line.amount_taxed,
                        'price_total': line.price_total,
                    }))
            elif model_name == 'ss.pipe':
                for line in getattr(order, line_attr):
                    order_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_uom_qty': line.pipe_kg_ft_qty,
                        'price_unit': line.price_unit * 20,
                        'cost_price': line.cost_price,
                        'profit_margin': line.profit_margin,
                        'price_subtotal': line.price_subtotal,
                        'tax_id': [(4, tax.id) for tax in line.tax_id],
                        'discount': line.discount,
                        'disc_percentage': line.disc_percentage,
                        'amount_taxed': line.amount_taxed,
                        'price_total': line.price_total,
                    }))
            else:
                for line in getattr(order, line_attr):
                    order_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_uom_qty': line.total_weight,
                        'price_unit': line.price_unit,
                        'cost_price': line.cost_price,
                        'profit_margin': line.profit_margin,
                        'price_subtotal': line.price_subtotal,
                        'tax_id': [(4, tax.id) for tax in line.tax_id],
                        'discount': line.discount,
                        'disc_percentage': line.disc_percentage,
                        'amount_taxed': line.amount_taxed,
                        'price_total': line.price_total,
                    }))
        return order_lines


    @api.depends('order_estimation_line', 'compute_lines_total')
    def _compute_amount_lines_total(self):
        for rec in self:

            rec.action_compute_estimation()
            rec.compute_lines_total = False



    def action_draft(self):
        self.state = "draft"

    def action_in_progress(self):
        self.state = "in_progress"

    def action_confirmed(self):
        self.state = "confirmed"

    def action_cancel(self):
        self.state = "cancel"


    @api.depends('total_amount', 'order_estimation_line', 'order_estimation_line.price_total')
    def _compute_total_amount(self):
        for rec in self:
            total_amount = 0
            for line in rec.order_estimation_line:
                total_amount += line.price_total

            if total_amount:
                rec.total_amount = total_amount
            else:
                rec.total_amount = False




    @api.depends('name', 'partner_id')
    def _compute_name(self):
        for rec in self:
            if rec.partner_id and rec.sequence:
                res = str(rec.partner_id.name) +' - '+ str(rec.sequence)
                rec.name = res
            else:
                rec.name = False




    def create_manufacturing_order(self):
        mo_lines = []
        for line in self.order_estimation_line:
            mo_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'product_uom_id': line.product_uom_id.id,
            }))

        created_bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_uom_id': self.product_tmpl_id.uom_id.id,
            'product_qty': self.product_qty,
            'code': self.name,
            'type': 'normal',
            'bom_line_ids': mo_lines
        })

        if created_bom:
            self.bom_id = created_bom.id
            self.is_mo = True

            mrp_order = self.env['mrp.production'].create({
                'product_qty': self.product_qty,
                'bom_id': created_bom.id,
                'is_estimation': True,
            })
            self.mrp_order = mrp_order.id


    def action_view_manufacturing_order(self):
        self.ensure_one()
        result = {
            "type": "ir.actions.act_window",
            "res_model": "mrp.production",
            "name": _("Manufacturing Order"),
            'view_mode': 'list,form',
            'domain': [('id', '=', self.mrp_order.id)],
        }
        return result



    @api.model
    def create(self, values):
        if values.get('sequence', _('New Order')) == _('New Order'):
            values['sequence'] = self.env['ir.sequence'].next_by_code('order.estimation') or _('New Order')
        res = super(OrderEstimation, self).create(values)
        return res

    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('Only cancelled record. You can Delete!'))
            if not rec.env.user.has_group('ssol_od_estimation.group_order_estimation_delete_access'):
                raise UserError(_('You can not delete this Maintenance Record. Contact your administrator.'))
            else:
                return super(OrderEstimation, self).unlink()


class OrderEstimationLine(models.Model):
    _name = 'order.estimation.line'


    order_id = fields.Many2one('order.estimation', string='Estimation Order Reference', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='order_id.company_id', store=True, index=True)
    product_id = fields.Many2one(comodel_name='product.product', check_company=True, domain=lambda self: self._product_id_domain())
    sr_no = fields.Integer(string="Sr No.", compute='_compute_sr_no', store=True)
    sr_no_char = fields.Char(string="Sr No.", compute='_compute_sr_no', store=True)
    name = fields.Text(string="Description",  store=True)

    product_uom_id = fields.Many2one(comodel_name='uom.uom', string="Unit of Measure", compute='_compute_product_uom_id',
        store=True, readonly=False, precompute=True,
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_uom_qty = fields.Float(string='Qty',digits=(16, 3), required=True, default=1)

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



    @api.depends('profit_margin', 'cost_price', 'product_id', 'product_uom_qty', 'price_unit')
    def _compute_cost_margin(self):
        for line in self:
            if line.product_id:
                cost_subtotal = line.product_id.standard_price * line.product_uom_qty
                line.cost_price = cost_subtotal
                unit_price_subtotal = line.price_unit * line.product_uom_qty
                line.profit_margin = (unit_price_subtotal - cost_subtotal)
            else:
                line.cost_price = False
                line.profit_margin = False


    # === CUSTOM COMPUTE METHODS ===#
    @api.depends('order_id.order_estimation_line', 'sr_no', 'sr_no_char')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            value_sr = 1
            for line in order.order_estimation_line:
                value_sr += 1

    @api.depends('product_id', 'price_unit', 'price_subtotal', 'product_uom_qty')
    def _compute_price_subtotal(self):
        for line in self:
            subtotal = line.price_unit * line.product_uom_qty
            line.price_subtotal = subtotal

    @api.depends('product_id', 'price_unit', 'price_subtotal', 'product_uom_qty', 'amount_taxed', 'tax_id')
    def _compute_amount_taxed(self):
        for rec in self:
            percentage_total = 0
            for line in rec.tax_id:
                percentage_total += line.amount
            taxed_amount = (rec.price_subtotal /100) * percentage_total
            rec.amount_taxed = rec.price_subtotal + taxed_amount

    @api.depends('product_id', 'price_unit', 'price_subtotal', 'product_uom_qty', 'amount_taxed', 'tax_id', 'price_total', 'discount', 'disc_percentage')
    def _compute_amount_total(self):
        for line in self:
            disc_percentage = (line.amount_taxed / 100) * line.disc_percentage
            line.price_total =  line.amount_taxed - (line.discount + disc_percentage)