from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from datetime import date


class Teacher(models.Model):
    _name = 'voca.teacher'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherit mail.thread and mail.activity.mixin

    # _description = 'Portal'

    name = fields.Char(string='Name', related='instructor.name')
    google_meet=fields.Char(string='Google Meet',readonly=False)
    zoom =fields.Char(string='Zoom', readonly=False)

    image_1920 = fields.Image(string="Image", readonly=False, related="instructor.image_1920")  # image.mixin override

    tag_ids = fields.Many2many('voca.teacher.tags', string='Tags', related='instructor.tag_ids',readonly=False)

    instructor = fields.Many2one('res.partner', string='Instructor')

    experience = fields.Char(string='Experience', related='instructor.experience',readonly=False)
    instrument=fields.Char(string='Instrument',related='instructor.instrument')
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


    def action_approved(self):
    
        for rec in self:
            if rec.state not in ['draft', 'refused']:
                raise UserError(_("Only teachers in the Draft or Refused state can be approved."))

            # Update the teacher's state to 'approved'
            rec.state = 'approved'

            # Activate the related user and assign internal user rights
            if rec.instructor:
                related_users = rec.instructor.user_ids
                internal_group = self.env.ref('base.group_user')  # Internal User group
                portal_group = self.env.ref('base.group_portal')  # Portal group

                for user in related_users:
                    user.sudo().write({
                        'active': True,  # Activate the user
                        'groups_id': [(3, portal_group.id), (4, internal_group.id)],  # Remove Portal group, add Internal User group
                    })


    def action_refused(self):
        
        for rec in self:
            if rec.state not in ['draft', 'approved']:
                raise UserError(_("Only teachers in the Draft or Approved state can be refused."))

            # Update the teacher's state to 'refused'
            rec.state = 'refused'

            # Remove internal user rights
            if rec.instructor:
                related_users = rec.instructor.user_ids
                internal_group = self.env.ref('base.group_user')  # Internal User group
                portal_group = self.env.ref('base.group_portal')  # Portal group (optional)

                for user in related_users:
                    # Remove Internal User group
                    user.sudo().write({
                        'groups_id': [(3, internal_group.id)],  # Remove Internal User group
                    })

                    # Optionally assign Portal group
                    if portal_group not in user.groups_id:
                        user.sudo().write({
                            'groups_id': [(4, portal_group.id)],  # Add Portal group
                        })

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



