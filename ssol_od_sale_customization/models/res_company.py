from odoo import models , api ,fields



class ResCompanyInheritOM(models.Model):
    _inherit = "res.company"

    strn = fields.Char(string="STRN")
