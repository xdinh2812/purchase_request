from odoo import models, fields, api


class PurchaseRequestReject(models.TransientModel):
    _name = 'purchase.request.reject.wizard'
    _description = 'Purchase Request Rejection Wizard'

    request_id = fields.Many2one('purchase.request', string='Purchase Request')
    reason = fields.Text('Rejection Reason', required=True)

    def action_reject(self):
        self.request_id.write({
            'state': 'cancel',
            'rejection_reason': self.reason
        })
        return {'type': 'ir.actions.act_window_close'}
