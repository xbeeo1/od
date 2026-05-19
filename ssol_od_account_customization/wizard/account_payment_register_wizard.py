# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    wht_total_amount = fields.Float(string="Total Amount")
    wh_tax_percentage = fields.Float(string="W.H.T %")
    wh_tax_amount = fields.Float(string="W.H.T Amount", compute='_compute_wht_tax')


    """ONCHANGE ON WHT PERCENTAGE AND CALCULATE WH TAX AMOUNT UPDATE PAYMENT AMOUNT"""
    @api.onchange('wh_tax_percentage','wht_total_amount')
    def _onchange_wh_tax_percentage(self):
        if self.wht_total_amount and self.wh_tax_percentage:
            percentage_amount = (self.wht_total_amount / 100) * self.wh_tax_percentage
            # self.wh_tax_amount = percentage_amount
            self.amount = self.wht_total_amount - percentage_amount


    # """ONCHANGE ON WHT TOTAL AMOUNT AND CALCULATE WH TAX AMOUNT UPDATE PAYMENT AMOUNT"""
    # @api.onchange('wht_total_amount')
    # def _onchange_wht_total_amount(self):
    #     if self.wht_total_amount and self.wh_tax_percentage:
    #         percentage_amount = (self.wht_total_amount / 100) * self.wh_tax_percentage
    #         # self.wh_tax_amount = percentage_amount
    #         self.amount = self.wht_total_amount - percentage_amount

    @api.depends('wht_total_amount', 'wh_tax_percentage')
    def _compute_wht_tax(self):
        for record in self:
            if record.wht_total_amount and record.wh_tax_percentage:
                record.wh_tax_amount = (record.wht_total_amount / 100) * record.wh_tax_percentage
                # record.amount = record.wht_total_amount - record.wh_tax_amount
            else:
                record.wh_tax_amount = 0.0


    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        vals.update({
            'wht_total_amount': self.wht_total_amount,
            'wh_tax_percentage': self.wh_tax_percentage,
            'wh_tax_amount': self.wh_tax_amount,
        })
        return vals