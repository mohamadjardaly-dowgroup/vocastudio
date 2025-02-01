from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class TeacherBooking(models.Model):
    _name = 'voca.teacher.booking.lines'
    # _description = 'Portal'
    _rec_name = 'availablity_date'


    name = fields.Char('Name', translate=True)
    #######samiha
    lesson_state = fields.Selection([
        ('draft', 'Draft'),
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled')
    ], string='Lesson State', default='draft', required=True)

    booking_id = fields.Many2one('voca.teacher', string='Teacher')
    booking_order_id = fields.Many2one('sale.order.line', string='Booking')

    availablity_date = fields.Datetime('Date', required=True)

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

    #samiha automation for completed lessons
    @api.model
    def mark_completed_bookings(self):
        """Marks past upcoming lessons as completed"""
        now = datetime.now()
        print("now ................. ", now)
        upcoming_bookings = self.search([
            ('lesson_state', '=', 'upcoming'),
            ('availablity_date', '<', now)
        ])
        if upcoming_bookings:
            upcoming_bookings.write({'lesson_state': 'completed'})
            return True
        return False

    @api.model
    def delete_old_draft_bookings(self):
        """Deletes teacher bookings that are still in 'draft' state after their availability date has passed."""
        now = datetime.now()
        old_draft_bookings = self.search([
            ('lesson_state', '=', 'draft'),
            ('availablity_date', '<', now)
        ])
        if old_draft_bookings:
            old_draft_bookings.unlink()
            return True
        return False
        

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
    




