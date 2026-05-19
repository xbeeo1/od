from email.policy import default

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import AccessError, ValidationError, UserError


class SaleOrderInheritOD(models.Model):
    _inherit = 'sale.order'

    od_ref = fields.Char(string="Ref", compute="_compute_od_ref",)

    @api.depends("partner_id", "name", "od_ref")
    def _compute_od_ref(self):
        for record in self:
            current_year = datetime.now().year % 100
            print('current_year', current_year)
            partner_short = record.partner_id.partner_short or "UNKNOWN"
            print('partner_short', partner_short)
            order_name = record.name or "S00000"
            print('order_name', order_name)
            record.od_ref = f"OD/{current_year}/{partner_short}/{order_name}"
            print('od_ref', record.od_ref)


    quotation_type = fields.Selection(string="Quotation Type", selection=[('copper_quotation', 'Copper Quotation'), ('nh3_quotation', 'NH3 Quotation'),('other_quotation', 'Other Quotation')])
    sub = fields.Char(string="Sub:",)
    sub_description = fields.Text(string="Note")

    report_type = fields.Selection(string="Report Type", selection=[('letter', 'With Letterhead'), ('w_letter', 'Without Letterhead'), ], required=False, )

    tube_material = fields.Text(string="TUBE material:", default='Seamless Copper tube ')
    total_no_tubes = fields.Text(string="Total No. of tubes:", default='840 No.')
    copper_tube_dia = fields.Text(string="Copper tube Dia:", default='9.5 mm')
    copper_tube_thickness = fields.Text(string="Copper tube Thickness:", default='0.71 mm')
    tube_type = fields.Text(string="Tube type: ", default='Plain tube ')
    tube_pitch = fields.Text(string="Tube Pitch:", default='Triangular ')
    tube_ends = fields.Text(string="Tube Ends: ", default='Expanded in tube sheets')
    copper_tube_origin = fields.Text(string="Copper Tube origin:", default='KOREA')
    fin_material = fields.Text(string="FIN material:", default='Copper Alloy ')
    fin_thickness = fields.Text(string="Fin thickness:", default='0.15 mm ')
    fin_temper = fields.Text(string="Fin temper:", default='Soft tempered ')
    fin_per_inch = fields.Text(string="Fin Per Inch:", default='As per sample')
    fin_pitch = fields.Text(string="Fins Pitch:", default='As per sample')
    width_of_fin = fields.Text(string="Width of fins:", default='As per sample')
    fin_ends = fields.Text(string="Fin Ends:", default='Plain')
    fin_coating = fields.Text(string="Fin Coating:", default='NO.')


    detailed_note = fields.Text(string="NOTE:")
    ex_price = fields.Text(string="EX")
    warranty = fields.Text(string="WARRANTY:", default='12 Months from the date of delivery Ex-works Lahore')
    warranty_02 = fields.Text(string="WARRANTY:", default='Supplied manufactured Equipment standard warranty twelve months from the date of delivery.')
    warranty_01 = fields.Text(string="WARRANTY:", default='Supplied manufactured Equipment standard warranty twelve months. Excluding all electrical items.')
    note_gst = fields.Text(string="NOTE:", default='18% G.S.T shall be charged on actual')
    payment = fields.Text(string="PAYMENT:", default='70% advance with valued P.O. balance before delivery Ex-works Lahore.')
    payment_01 = fields.Text(string="PAYMENT:", default='60% advance with valued P.O. 30% against delivery Ex. Works Lahore & 10% 15 days after commissioning')
    delivery = fields.Text(string="DELIVERY:", default='within 04 to 05 working weeks, after receiving Old Cooler with valued P.O. & Advance payment.(Transportation not included)')
    delivery_02 = fields.Text(string="DELIVERY:", default='within 03 to 04 working weeks after receiving valued PO & Advance payment. (Delivery not included)')
    delivery_01 = fields.Text(string="DELIVERY:", default='within 16 to 18 working weeks, after receiving valued PO & Advance payment.')
    validity = fields.Text(string="VALIDITY:", default='07 days only OR due to extreme forex fluctuation, above mentioned prices are subject to change based on market situation.')
    validity_01 = fields.Text(string="VALIDITY:", default='04 days only or due to extreme forex fluctuation, rise in USD > Rs. 2 will reflect in above mentioned Prices without any intimation')
    force_majeure = fields.Text(string="FORCE MAJEURE:", default='OMERDRAZ ENGINEERING COMPANY will not be responsible for failure to meet the delivery schedules of the contract nor for any losses or damages to the Client (or any third party/person) occasioned by delay in the performance or the non-performance of any OMERDRAZ’s obligations under the order, or by loss of or any damage to the material when caused directly or indirectly by, or in any manner arising from the act of God, acts of government or military authority, casualty, riots, Lockdown, strikes, sabotage, terrorism or any other similar or different cause or causes beyond OMERDRAZ’s control or of its suppliers or sub-contractors / vendors. Force Majeure will extend the time of OMERDRAZ’s execution of the work, and give it the right to make price adjustments, if necessary, under the contract by the effects of such Force Majeure event considering the necessary restart period on the performance of OMERDRAZ’s or its suppliers or sub-contractors / vendors.')

    best_regards_for = fields.Text(string="Best Regards For", default='OMERDRAZ ENGINEERING CO LAHORE.')
    note_best_regard = fields.Text(string="NOTE", default='THIS IS COMPUTER GENERATED DOCUMENT NO SIGNATRE REQUIRED')


    # NH3 Quotation Extra Fields
    # points = fields.Text(string='Points', translate=True)
    your_agreements = fields.Text(string="YOURS ARRANGEMENT", default='Masonry work (Foundation etc.), Water supply, Electricity supply 3 phase for ammonia plant & up to Penal board Main breakers, water treatment plant if required. Ammonia Gas, Compressor Oil, P.P Glycol. Transportation, any local taxes duties etc, material unloading up to foundations, Accommodation, Food & Medical if required for 3 to 4 workers during work at site, Any Material leftover after commissioning of the Glycol system at site will be the property of the M/s OMERDRAZ ENGINEERING CO. LAHORE. Or any other item which is not clearly mentioned in our quotation will be provide by the client.') # after force_majeure


    # Other Quotation Extra Fields
    detailed = fields.Text(string='Detailed', translate=True)
    gm = fields.Text(string='GM : ', translate=True, default='ZAHID HUSSAIN MUGHAL')

    # Bill Quotation Extra Fields
    price_bill_report = fields.Text(string="TOTAL PRICE")
    general_sales_tax = fields.Text(string="General Sales Tax")
    note_bill_report = fields.Text(string="Payment Note")


    def _prepare_invoice(self):
        invoice_vals = super(SaleOrderInheritOD, self)._prepare_invoice()
        invoice_vals['od_ref'] = self.od_ref
        return invoice_vals


