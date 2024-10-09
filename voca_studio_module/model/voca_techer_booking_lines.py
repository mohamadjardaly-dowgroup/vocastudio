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
            print("daaate ", rec.availablity_date)
            rec.status = 'approved'
    def action_refused(self):
        for rec in self:
            rec.status = 'refused'

    @api.constrains('availablity_date')
    def _check_unique_availablity_date(self):
        for rec in self:
            existing_booking = self.search([
                ('availablity_date', '=', rec.availablity_date),
                ('id', '!=', rec.id)  # Exclude the current record
            ])
            if existing_booking:
                raise ValidationError(
                    _('The availability date must be unique. A booking already exists for this date: %s') % rec.availablity_date)