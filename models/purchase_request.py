from odoo import fields, models, api
from odoo.exceptions import UserError
import xlsxwriter
from io import BytesIO
import base64


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Yêu cầu mua hàng'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Request Reference', required=True, copy=False, readonly=True,
                       default=lambda self: 'New')
    department_id = fields.Many2one('hr.department', string='Department', required=True,
                                    default=lambda self: self.env.user.employee_id.department_id)
    request_id = fields.Many2one('res.users', string='Requestor', required=True,
                                 default=lambda self: self.env.user)
    approve_id = fields.Many2one('res.users', string='Approve', required=True)
    date = fields.Date(string='Request Date', default=fields.Date.today, required=True)
    date_approve = fields.Date(string='Approval Date', readonly=True)
    description = fields.Text('Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('wait', 'Waiting'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    request_line_id = fields.One2many('purchase.request.line', 'request_id',
                                       string='Request Lines')
    total_qty = fields.Float(string='Total Quantity', compute='_compute_totals', store=True)
    total_amount = fields.Float(string='Total Amount', compute='_compute_totals', store=True)

    def action_approve(self):
        self.write({
            'state': 'approved',
            'date_approve': fields.Date.today()
        })

    def action_send_request(self):
        self.ensure_one()
        if not self.request_line_id:
            raise UserError('You cannot send an empty purchase request')
        self.state = 'wait'

    def action_draft(self):
        self.ensure_one()
        self.state = 'draft'

    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancelled'

    def action_reject(self):
        return {
            'name': 'Reject Purchase Request',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.request_id.id}
        }

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError('You can only delete draft purchase request')
        return super(PurchaseRequest, self).unlink()

    @api.depends('request_line_id')
    def _compute_totals(self):
        for rec in self:
            rec.total_amount = sum(rec.request_line_id.mapped('total'))
            rec.total_qty = sum(rec.request_line_id.mapped('qty'))

    @api.onchange('department_id')
    def _onchange_department(self):
        if self.department_id:
            manager = self.department_id.manager_id.user_id
            if manager:
                self.approve_id = manager

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or 'New'
        return super(PurchaseRequest, self).create(vals)

    def export_to_excel(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Purchase Request Details")

        # Định dạng
        bold = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
        currency_format = workbook.add_format({
            'num_format': '#,##0',
            'align': 'right',
            'border': 1
        })
        number_format = workbook.add_format({'align': 'right', 'border': 1})
        total_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'border': 1
        })

        # Thiết lập độ rộng cột
        sheet.set_column('A:A', 5)   # STT
        sheet.set_column('B:B', 15)  # Mã SP
        sheet.set_column('C:C', 40)  # Tên SP
        sheet.set_column('D:D', 10)  # Số lượng
        sheet.set_column('E:E', 15)  # Đơn vị
        sheet.set_column('F:G', 15)  # Giá và Thành tiền

        # Tiêu đề cột
        headers = ['STT', 'Mã Sản Phẩm', 'Tên Sản Phẩm', 'Số Lượng',
                  'Đơn Vị Tính', 'Giá Đơn Vị', 'Thành Tiền']
        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header, bold)

        # Ghi dữ liệu
        row = 1
        try:
            for index, line in enumerate(self.request_line_id, start=1):
                sheet.write(row, 0, index, number_format)
                sheet.write(row, 1, line.product_id.default_code or '', number_format)
                sheet.write(row, 2, line.product_id.name)
                sheet.write(row, 3, line.qty, number_format)
                sheet.write(row, 4, line.uom_id.name)
                sheet.write(row, 5, line.price_unit, currency_format)
                sheet.write(row, 6, line.qty * line.price_unit, currency_format)
                row += 1

            # Tổng cộng
            sheet.write(row, 2, "Tổng Cộng", total_format)
            sheet.write(row, 3, sum(line.qty for line in self.request_line_id),
                       total_format)
            sheet.write(row, 6, sum(line.qty * line.price_unit
                       for line in self.request_line_id), currency_format)

        except Exception as e:
            # Log lỗi nếu cần
            raise e

        workbook.close()
        output.seek(0)

        # Tạo tên file
        filename = f'Purchase_Request_{self.name}.xlsx'

        # Trả về file excel
        return {
            'type': 'ir.actions.act_url',
            'url': f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{base64.b64encode(output.getvalue()).decode()}',
            'target': 'self',
            'name': filename,
        }
