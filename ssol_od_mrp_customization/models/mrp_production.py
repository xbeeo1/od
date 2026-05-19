# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class MrpProductionInheritOD(models.Model):
    _inherit = 'mrp.production'


    report_type = fields.Selection(string="Test Report Type", selection=[('test_report_msc', 'Test Report for MS Coil'),
                                                                         ('test_report_cooler', 'Test Report Cooler heat'),
                                                                         ('both', 'Both Reports')])

    # state = fields.Selection(selection_add=[('quality_check', 'Quality Check')])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('progress', 'In Progress'),
        ('to_close', 'To Close'),
        ('quality_check', 'Quality Check'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        compute='_compute_state', copy=False, index=True, readonly=True,
        store=True, tracking=True,
        help=" * Draft: The MO is not confirmed yet.\n"
             " * Confirmed: The MO is confirmed, the stock rules and the reordering of the components are trigerred.\n"
             " * In Progress: The production has started (on the MO or on the WO).\n"
             " * To Close: The production is done, the MO has to be closed.\n"
             " * Done: The MO is closed, the stock moves are posted. \n"
             " * Cancelled: The MO has been cancelled, can't be confirmed anymore.")



    ref_no = fields.Char(string="Ref No")
    date_tr = fields.Date(string="Date")
    for_m_s = fields.Char(string="FOR M/s")
    po_number = fields.Char(string="PO #")
    address_tr = fields.Text(string="Add")
    serial_tr = fields.Char(string="Serial #")
    ms_pipe_tube_dia = fields.Text(string="MS PIPE/TUBE  DIA")
    ms_pipe_hdg = fields.Char(string="MS PIPE HOT DIP GALVANIZED")
    ref_od_drawing = fields.Char(string="REF: OMERDRAZ Drawing#")
    overall_coil_lengths = fields.Char(string="Overall Coils Length")
    overall_coil_height = fields.Char(string="Overall Coils Height")
    header_od_dia = fields.Char(string="Header OD Dia")
    overall_header_lengths = fields.Char(string="Overall Header Length")
    header_connection = fields.Char(string="Header connection Center to center")
    total_coil_in_bundles = fields.Char(string="Total No. of Coils / Stands in Bundle")
    pressure_no_gcc_no = fields.Char(string="Pressure Gauge calibration certificate No")
    gauge_calibration_dd = fields.Date(string="Gauge Calibration due date:")
    used_for = fields.Selection(string="PRESSURE TEST", selection=[('hydraulically', 'Hydraulically'),
                                                                    ('air', 'Air'), ('nitrogen', 'Nitrogen')])  # widget= "radio"
    test_pressure = fields.Char(string="Test pressure")
    pressure_start_time = fields.Char(string="Pressure Start time")  # widget= "float_time"
    pressure_end_time = fields.Char(string="Pressure End time")  # widget= "float_time"
    pressure_holding_time = fields.Char(string="Pressure Holding time")  # widget= "float_time"
    temp_during_testing = fields.Char(string="Temp. During testing")
    test_result = fields.Selection(string="TEST RESULT", selection=[('satisfactory', 'Satisfactory'), ('rejected', 'Rejected'), ]) # widget= "radio"
    remarks_tr = fields.Text(string="REMARKS")

    # name_tr = fields.Char(string="Name")  # group name INSPECTION
    name_tr = fields.Selection(string="Name", selection=[('none', ''),('zahid_hussain', 'Zahid Hussain'), ('ziad_mughal', 'Ziad Mughal')])
    signature_tr = fields.Char(string="Signature:")
    date_inspection_tr = fields.Date(string="Date")

    name_tp_tr = fields.Char(string="Name")  # group name THIRD PARTY INSPECTION
    signature_tp_tr = fields.Char(string="Signature")
    date_inspection_rp_tr = fields.Date(string="Date")



    # FIELDS FOR COPPER QUALITY CHECK TAB
    ref_noc = fields.Char(string="Ref No")
    date_trc = fields.Date(string="Date")
    for_m_sc = fields.Char(string="FOR M/s")
    po_number_c = fields.Char(string="PO #")
    po_number_client = fields.Char(string="Client's PO #")
    dated_trc = fields.Date(string="Dated")
    address_trc = fields.Text(string="Add")


    model_make = fields.Char(string="Model / Make")
    cooler_id = fields.Char(string="Cooler ID#")
    frame_material = fields.Char(string="Frame Material")
    frame = fields.Selection(string="Frame", selection=[('new_frame', 'New Frame'), ('old_frame', 'Old Frame')])
    tube_sheet_material = fields.Char(string="End Plate / Tube sheet Material")
    stack_size = fields.Char(string="Stack Size")
    no_of_stacks = fields.Char(string="No. of Stacks")
    refurbished = fields.Char(string="Refurbished")

    tube_material = fields.Char(string="TUBE Materia")
    tube_size = fields.Char(string="Tube Size")
    no_of_tubes = fields.Char(string="No of Tubes")
    no_tubes = fields.Boolean(string="No Tubes")
    no_of_rows = fields.Char(string="No of Rows")
    no_of_tubes_each_row = fields.Char(string="No. of Tubes Each Row")
    total_no_of_tubes = fields.Char(string="Total No. of Tubes")
    length_of_tube = fields.Char(string="Length of Tube")
    total_weight_tubes = fields.Char(string="Total weight of copper tubes")
    make_origin = fields.Char(string="Make/Origin")

    fins_type = fields.Selection(string="Finns", selection=[('copper_fins', 'COPPER FINS'),
                                                            ('aluminum_fins', 'ALUMINIUM FINS'),
                                                            ('no_fin', 'NO FIN'),
                                                            ])

    fin_coating = fields.Selection(string="FIN COATING ", selection=[('nickle', 'NICKLE'),
                                                            ('tin', 'TIN')])
    about_hours_for = fields.Char(string="For")
    fin_detail = fields.Html(string="Fin Detail")

    total_no_fin = fields.Char(string="Total No. Fin")
    fins_inch = fields.Char(string="Fins/inch")
    fin_weight = fields.Char(string="Weight")
    tube_expand_by = fields.Char(string="Tube Expand by")
    pressure_test_at = fields.Char(string="Pressure Test at")
    pressure_test = fields.Selection(string="PRESSURE TEST", selection=[('hydraulically', 'Hydraulically'),
                                                                   ('air', 'Air'),
                                                                   ('nitrogen', 'Nitrogen')])  # widget= "radio"

    # name_trc = fields.Char(string="Name")  # group name INSPECTION
    name_trc = fields.Selection(string="Name", selection=[('none', ''), ('zahid_hussain', 'Zahid Hussain'),
                                                         ('ziad_mughal', 'Ziad Mughal')])
    signature_trc = fields.Char(string="Signature:")
    date_inspection_trc = fields.Date(string="Date")

    name_tp_trc = fields.Char(string="Name")  # group name THIRD PARTY INSPECTION
    signature_tp_trc = fields.Char(string="Signature")
    date_inspection_rp_trc = fields.Date(string="Date")




    def action_quality_check(self):
        self.state = 'quality_check'