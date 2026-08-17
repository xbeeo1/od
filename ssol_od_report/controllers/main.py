import io
from datetime import datetime

import xlsxwriter

from odoo import http
from odoo.http import request, content_disposition


class WHTReportController(http.Controller):

    @http.route('/wht_report/xlsx', type='http', auth='user')
    def wht_report_xlsx(self, date_from=None, date_to=None, partner_id=None, **kw):
        domain = [
            ('state', '=', 'posted'),
            ('partner_id.customer_rank', '>', 0),
        ]
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        if partner_id:
            domain.append(('partner_id', '=', int(partner_id)))

        payments = request.env['account.payment'].sudo().search(domain, order='date asc')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('W.H.T Report')

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
        })
        label_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
        })
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9D9D9',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        cell_format = workbook.add_format({'border': 1})
        sr_format = workbook.add_format({'border': 1, 'align': 'center'})
        number_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        percent_format = workbook.add_format({'border': 1, 'num_format': '0.00"%"'})

        def fmt_date(date_str):
            if not date_str:
                return ''
            d = datetime.strptime(date_str, '%Y-%m-%d')
            return d.strftime('%d %B %Y')

        col_widths = [6, 15, 18, 30, 15, 10, 15, 15]
        for col, width in enumerate(col_widths):
            sheet.set_column(col, col, width)

        # Row 0: Title
        sheet.merge_range(0, 0, 0, 7, 'W.H.T Report', title_format)

        # Row 1: Date From / Date To
        sheet.merge_range(1, 0, 1, 3, f'Date From: {fmt_date(date_from)}', label_format)
        sheet.merge_range(1, 4, 1, 7, f'Date To: {fmt_date(date_to)}', label_format)

        # Row 2: spacer (blank)

        # Row 3: Table headers
        header_row = 3
        headers = [
            'Sr#', 'Date', 'Number', 'Customer',
            'Total Amount', 'W.H.T%', 'W.H.T Amount', 'Amount Signed',
        ]
        sheet.write(header_row, 0, 'Sr#', header_format)
        for col, header in enumerate(headers):
            sheet.write(header_row, col, header, header_format)

        # Data rows
        row = header_row + 1
        for i, payment in enumerate(payments, start=1):
            sheet.write(row, 0, i, sr_format)
            sheet.write(row, 1, fmt_date(str(payment.date) if payment.date else ''), cell_format)
            sheet.write(row, 2, payment.name or '', cell_format)
            sheet.write(row, 3, payment.partner_id.name or '', cell_format)
            sheet.write(row, 4, payment.wht_total_amount or 0.0, number_format)
            sheet.write(row, 5, payment.wh_tax_percentage or 0.0, percent_format)
            sheet.write(row, 6, payment.wh_tax_amount or 0.0, number_format)
            sheet.write(row, 7, payment.amount or 0.0, number_format)
            row += 1

        workbook.close()
        output.seek(0)
        xlsx_data = output.read()
        output.close()

        return request.make_response(
            xlsx_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition('WHT_Report.xlsx')),
                ('Content-Length', len(xlsx_data)),
            ],
        )