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
            ('booked', 'Booked'),
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

    #samiha check for the same teacher not globally 
    @api.constrains('availablity_date', 'booking_id')
    def _check_unique_availability_date(self):
        for rec in self:
            existing_booking = self.search([
                ('availablity_date', '=', rec.availablity_date),
                ('booking_id', '=', rec.booking_id.id),
                ('id', '!=', rec.id)  #if not the system will find this current record and cosider it as a duplicate
            ])
            if existing_booking:
                raise ValidationError(
                    _('The availability date must be unique for the same teacher. '
                    'Teacher %s already has a booking for this date: %s') % (rec.booking_id.name, rec.availablity_date)
                )
