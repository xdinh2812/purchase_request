from odoo import fields, models, api


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _description = 'Chi tiết yêu cầu mua hàng'

    request_id = fields.Many2one('purchase.request', string='Purchase Request', required=True)
    product_id = fields.Many2one('product.template', string='Product', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    qty = fields.Float('Requested Quantity', required=True)
    qty_approve = fields.Float('Approved Quantity')
    price_unit = fields.Float('Unit Price')
    total = fields.Float('Total', compute='_compute_total', store=True)
    state = fields.Selection(related='request_id.state')

    @api.depends('qty', 'price_unit')
    def _compute_total(self):
        for line in self:
            line.total = line.qty * line.price_unit

    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            # Get latest supplier price
            supplier_info = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', self.product_id.id)
            ], order='date_start desc', limit=1)
            if supplier_info:
                self.price_unit = supplier_info.price
