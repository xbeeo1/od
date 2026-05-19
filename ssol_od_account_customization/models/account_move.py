# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from num2words import num2words


class AccountMoveInheritEF(models.Model):
    _inherit = 'account.move'
    _description = 'account.move.inherit'

    bank_name = fields.Many2one(comodel_name="res.bank", string="Bank Name", required=False, )
    account_title = fields.Many2one(comodel_name="res.partner", string="Account Title", required=False, )
    account_number = fields.Char(string="Account Number")
    vendor_code = fields.Char(string="Vendor Code")
    gst_jurisdiction = fields.Char(string="GST Jurisdiction")
    hs_code = fields.Char(string="HS Code")
    wh_code = fields.Char(string="WHT Deduction")
    od_auth_sign = fields.Char(string="Name")
    po_number = fields.Char(string="PO Number")
    dc_number = fields.Char(string="DC Number")
    od_ref = fields.Char(string="OD Ref",  readonly=False,)
    sub = fields.Char(string="Sub", readonly=False)
    bill_invoice_field = fields.Char(string="Bill Invoice", readonly=False)
    points = fields.Html(string='Points', translate=True, readonly=False)
    price_bill_report = fields.Char(string="TOTAL PRICE", readonly=False)
    general_sales_tax = fields.Char(string="General Sales Tax", readonly=False)
    note_bill_report = fields.Char(string="Payment Note", readonly=False)
    ex_price = fields.Html(string="EX", readonly=False)
    best_regards_for = fields.Char(string="Best Regards For", readonly=False)
    other_detail = fields.Text(string="Other Details", required=False,)
    gm = fields.Char(string='GM : ', translate=True, readonly=False)
    is_background = fields.Boolean(string="WHT Exemption", default=False)


    territory_id = fields.Char(string="Territory")


    def _get_bank_address_vals(self, bank):

        if not bank:
            return {}
        return {
            'street_name': bank.street or '',
            'additional_street_name': bank.street2 or '',
            'city_name': bank.city or '',
            'postal_zone': bank.zip or '',
            'country_subentity': bank.state.name or '',
            'country_subentity_code': bank.state.code or '',
            'country': bank.country.name or '',
        }

    def _get_formatted_bank_address(self):

        bank_address_vals = self._get_bank_address_vals(self.bank_name)
        address = f"{bank_address_vals.get('street_name', '')}, " \
                  f"{bank_address_vals.get('additional_street_name', '')}, " \
                  f"{bank_address_vals.get('city_name', '')}, " \
                  f"{bank_address_vals.get('postal_zone', '')}, " \
                  f"{bank_address_vals.get('country_subentity', '')}, " \
                  f"{bank_address_vals.get('country', '')}"
        return address.strip(", ")








