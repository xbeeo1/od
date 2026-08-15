from odoo import models, fields


class WHTReportWizard(models.TransientModel):
    _name = 'wht.report.wizard'
    _description = 'WHT Report Wizard'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner'
    )

    def action_generate_xlsx(self):
        self.ensure_one()
        url = (
            '/wht_report/xlsx'
            f'?date_from={self.date_from}'
            f'&date_to={self.date_to}'
        )
        if self.partner_id:
            url += f'&partner_id={self.partner_id.id}'
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }
