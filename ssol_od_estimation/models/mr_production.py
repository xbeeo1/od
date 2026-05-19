from odoo import models , api ,fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta



class MrpProductionInherit(models.Model):
    _inherit = "mrp.production"

    is_estimation = fields.Boolean(string="Is Estimation")


    def action_view_estimation(self):
        self.ensure_one()
        result = {
            "type": "ir.actions.act_window",
            "res_model": "order.estimation",
            "name": _("Order Estimation"),
            'view_mode': 'list,form',
            'domain': [('mrp_order', '=', self.id)],
        }
        return result