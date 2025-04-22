from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from datetime import date, datetime, timedelta


class Teacher(models.Model):
    _name = 'voca.teacher'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherit mail.thread and mail.activity.mixin

    # _description = 'Portal'

    duration = fields.Integer(string="Lesson Duration (minutes)", default=45)
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
    schedule_ids = fields.One2many('voca.teacher.schedule', 'teacher_id', string="Weekly Schedule")

    name = fields.Char(string='Name', related='instructor.name')
    google_meet=fields.Char(string='Google Meet',readonly=False)
    zoom =fields.Char(string='Zoom', readonly=False)
    youtube_video=fields.Char(string='Video',readonly=False)
    youtube_videos = fields.One2many("voca.teacher.video", "teacher_id", string="YouTube Videos")

    image_1920 = fields.Image(string="Image", readonly=False, related="instructor.image_1920")  # image.mixin override

    tag_ids = fields.Many2many('voca.teacher.tags', string='Tags', related='instructor.tag_ids',readonly=False)

    instructor = fields.Many2one('res.partner', string='Instructor')

    experience = fields.Char(string='Experience', related='instructor.experience',readonly=False)
    instrument=fields.Char(string='Instrument',related='instructor.instrument',readonly=False)
    lang=fields.Char(string='Languages')

    categories = fields.Many2many('voca.teacher.categories', string='Category', related='instructor.category_ids',readonly=False,required=True)

    language = fields.Selection([
        ('en', 'English'),
        ('ar', 'Arabic'),
    ], string="Language")

    language_ids = fields.Many2many('res.lang',string="Language")

    about = fields.Char(string='About', related='instructor.about',readonly=False)
    learning_bio = fields.Char(string='Learn bio')
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
        ], string='Status', index=True, readonly=True, copy=False,
        default='draft', tracking=True)

    booking_ids= fields.One2many('voca.teacher.booking.lines', 'booking_id', string='Booking')
    packaging_ids= fields.One2many('voca.teacher.packaging.lines', 'package_id', string='Packaging')

    available_time_slots_ids = fields.Many2many('teacher.time.slots',
                                                string='Time Slots',
                                                help='Time slots of the movie')

    attachment_ids = fields.Many2many('ir.attachment' ,string="Upload Cv", related='instructor.attachment_ids',readonly=False)
    attachment_video_ids = fields.Many2many('ir.attachment' ,string="Video" ,readonly=False)

    product_id = fields.Many2one('product.product', string='Product', readonly=True)

    #samiha import datetime, timedelta
    def generate_booking_lines(self):
        BookingLine = self.env['voca.teacher.booking.lines']

        for teacher in self:
            if not (teacher.date_start and teacher.date_end and teacher.duration and teacher.schedule_ids):
                continue  # Skip if missing any necessary field

            # Clear old booking lines if needed (optional)
            # teacher.booking_ids.unlink()

            current_date = teacher.date_start
            while current_date <= teacher.date_end:
                weekday_str = str(current_date.weekday())  # 0 = Monday, ..., 6 = Sunday

                # Find all schedule templates for this weekday
                day_schedules = teacher.schedule_ids.filtered(lambda s: s.weekday == weekday_str)
                for schedule in day_schedules:
                    start_time = schedule.time_from
                    end_time = schedule.time_to

                    # Convert to datetime on current date
                    dt_start = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=start_time)
                    dt_end = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=end_time)

                    while dt_start + timedelta(minutes=teacher.duration) <= dt_end:
                        # Check if booking already exists for this teacher and date
                        exists = BookingLine.search_count([
                            ('booking_id', '=', teacher.id),
                            ('availablity_date', '=', dt_start)
                        ])
                        if not exists:
                            BookingLine.create({
                                'booking_id': teacher.id,
                                'availablity_date': dt_start,
                            })
                        dt_start += timedelta(minutes=teacher.duration)

                current_date += timedelta(days=1)



    def action_approved(self):
    
        for rec in self:
            if rec.state not in ['draft', 'refused']:
                raise UserError(_("Only teachers in the Draft or Refused state can be approved."))

            # Update the teacher's state to 'approved'
            rec.state = 'approved'

            # Activate the related user and assign internal user rights
            # if rec.instructor:
            #     related_users = rec.instructor.user_ids
            #     internal_group = self.env.ref('base.group_user')  # Internal User group
            #     portal_group = self.env.ref('base.group_portal')  # Portal group

            #     for user in related_users:
            #         user.sudo().write({
            #             'active': True,  # Activate the user
            #             'groups_id': [(3, portal_group.id), (4, internal_group.id)],  
            #         })


    def action_refused(self):
        
        for rec in self:
            if rec.state not in ['draft', 'approved']:
                raise UserError(_("Only teachers in the Draft or Approved state can be refused."))

            # Update the teacher's state to 'refused'
            rec.state = 'refused'

            # Remove internal user rights
            # if rec.instructor:
            #     related_users = rec.instructor.user_ids
            #     internal_group = self.env.ref('base.group_user')  # Internal User group
            #     portal_group = self.env.ref('base.group_portal')  # Portal group (optional)

            #     for user in related_users:
            #         
            #         user.sudo().write({
            #             'groups_id': [(3, internal_group.id)],  # Remove Internal User group
            #         })

                    
            #         if portal_group not in user.groups_id:
            #             user.sudo().write({
            #                 'groups_id': [(4, portal_group.id)],  # Add Portal group
            #             })

    @api.model
    def create(self, vals):
        package = super(Teacher, self).create(vals)
        # Automatically create a product linked to this package
        print("vaaaals ", vals, package.name)
        product_vals = {
            'name':  f"{package.name} - Lessons" ,
            'type': 'service',
            'is_published':True,
            # 'list_price': package.price,
        }
        product = self.env['product.product'].create(product_vals)
        package.product_id = product.id
        return package



