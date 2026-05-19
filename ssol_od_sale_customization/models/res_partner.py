from odoo import models , api ,fields, _


class ResPartnerInheritOM(models.Model):
    _inherit = "res.partner"


    partner_strn = fields.Char(string="STRN")
    partner_short = fields.Char(string="Contact Short Form")