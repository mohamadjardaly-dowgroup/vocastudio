from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from datetime import date


class Teacher(models.Model):
    _name = 'voca.teacher'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherit mail.thread and mail.activity.mixin

    # _description = 'Portal'

    name = fields.Char(string='Name', related='instructor.name')

    image_1920 = fields.Image(string="Image", readonly=False, related="instructor.image_1920")  # image.mixin override

    tag_ids = fields.Many2many('voca.teacher.tags', string='Tags', related='instructor.tag_ids',readonly=False)

    instructor = fields.Many2one('res.partner', string='Instructor')

    experience = fields.Char(string='Experience', related='instructor.experience',readonly=False)

    categories = fields.Many2many('voca.teacher.categories', string='Category', related='instructor.category_ids',readonly=False)

    language = fields.Selection([
        ('en', 'English'),
        ('ar', 'Arabic'),
    ], string="Language")

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
            rec.state = 'approved'

    def action_refused(self):
        for rec in self:
            rec.state = 'refused'

    @api.model
    def create(self, vals):
        package = super(Teacher, self).create(vals)
        # Automatically create a product linked to this package
        print("vaaaals ", vals, package.name)
        product_vals = {
            'name':  f"{package.name} - Lessons" ,
            'type': 'service',
            # 'list_price': package.price,
        }
        product = self.env['product.product'].create(product_vals)
        package.product_id = product.id
        return package



