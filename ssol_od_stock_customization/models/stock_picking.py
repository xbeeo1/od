# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta, datetime, timezone
from datetime import timedelta
from odoo.fields import Datetime



class StockPickingInheritOD(models.Model):
    _inherit = 'stock.picking'
    _description = 'stock.picking.inherit'


    dc_number = fields.Char(string="Po Number #")
    do_sub = fields.Char(string="Sub")

    sending_material_through = fields.Char(string="Sending Material Through")
    freight_rent_advance = fields.Char(string="FREIGHT")

    do_note = fields.Char(string="Note")

    regard_for = fields.Char(string="For")