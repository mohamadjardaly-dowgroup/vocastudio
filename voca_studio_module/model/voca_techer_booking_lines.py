from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TeacherBooking(models.Model):
    _name = 'voca.teacher.booking.lines'
    # _description = 'Portal'
    _rec_name = 'availablity_date'


    name = fields.Char('Name', translate=True)

    booking_id = fields.Many2one('voca.teacher', string='Teacher')
    booking_order_id = fields.Many2one('sale.order.line', string='Booking')

    availablity_date = fields.Datetime('Date')

    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
        ], string='Status', index=True, readonly=True, copy=False,
        default='draft', tracking=True)


    def action_approved(self):
        for rec in self:
            rec.status = 'approved'
    def action_refused(self):
        for rec in self:
            rec.status = 'refused'