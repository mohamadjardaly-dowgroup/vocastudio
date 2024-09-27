from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Teacher(models.Model):
    _name = 'voca.teacher'
    # _description = 'Portal'

    name = fields.Char(string='Name',related='instructor.name' )

    image_1920 = fields.Image(string="Image",store=True, readonly=False)  # image.mixin override

    tag_ids = fields.Many2many('voca.teacher.tags', string='Tags)

#     tag_ids = fields.Many2many(
#     'voca.teacher.tags', 
#     'voca_teacher_tags_rel',  
#     'teacher_id', 
#     'tag_id',  
#     string='Tags'
# )

    instructor = fields.Many2one('res.partner',string='Instructor')

    experience = fields.Char(string='Experience',related='instructor.experience'  )


#     categories = fields.Many2many(
#    'voca.teacher.categories', 
#     'voca_teacher_categories_rel',  # Explicit relation table name
#     'teacher_id',  # Column for the model you're working on
#     'cat_id',      # Column for the 'voca.teacher.tags' model
#     string='Tags'
# )

    categories = fields.Many2many('voca.teacher.categories',string='Category',related='instructor.category_ids' )

    language = fields.Selection([
            ('en', 'English'),
            ('ar', 'Arabic'),
        ], string="Language")

    about = fields.Char(string='About',related='instructor.about')
    learning_bio = fields.Char(string='Learn bio')
    slot_ids = fields.One2many('voca.teacher.slots', 'slot_id', string='Direct subordinates')

