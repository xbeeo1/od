from odoo import models , api ,fields, _


class ResPartnerInheritOD(models.Model):
    _inherit = "res.partner"

    user_signature = fields.Binary(string="Signature")
