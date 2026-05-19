# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class MaterialType(models.Model):
    _name = "material.type"
    _description = "Material Type"

    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description")
