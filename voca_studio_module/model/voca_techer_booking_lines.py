from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import pytz

class TeacherBooking(models.Model):
    _name = 'voca.teacher.booking.lines'
    # _description = 'Portal'
    _rec_name = 'availablity_date'


    name = fields.Char('Name', translate=True)
    #######samiha
    
    booking_type = fields.Selection(
        [
            ("private_lesson", "Private Lesson"),
            ("lesson_program", "Lesson Program"),
        ],
        string="Booking Type",
        default="private_lesson",
        required=True,
    )

    lesson_program_id = fields.Many2one(
        "voca.lesson.program",
        string="Lesson Program",
    )

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
        default='approved', tracking=True)

    lesson_date_local = fields.Char(string="Lesson Date (Local)", compute="_compute_lesson_dates", store=False)

    
    @api.depends('availablity_date')
    def _compute_lesson_dates(self):
        """Compute lesson dates in both UTC and student’s timezone"""
        for record in self:
            if record.availablity_date:
                # Convert to UTC

                # Get student's timezone
                student_tz = record.booking_order_id.order_id.partner_id.tz or 'UTC'
                try:
                    tz = pytz.timezone(student_tz)
                    local_date = pytz.utc.localize(record.availablity_date).astimezone(tz)
                    record.lesson_date_local = local_date.strftime('%d %B %Y, %I:%M %p')
                    print("local_date ", local_date)
                    print("record.lesson_date_local ", record.lesson_date_local)
                except Exception:
                    record.lesson_date_local = record.availablity_date


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
    




