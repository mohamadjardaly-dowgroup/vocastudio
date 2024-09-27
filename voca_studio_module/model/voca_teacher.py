from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Teacher(models.Model):
    _name = 'voca.teacher'
    # _description = 'Portal'

    name = fields.Char(string='Title', required=True)

    image_1920 = fields.Image(string="Image",store=True, readonly=False)  # image.mixin override

    tag_ids = fields.Many2many('voca.teacher.tags', string='Tags')

    instructor = fields.Many2one('res.users',string='Instructor', required=True)

    experience = fields.Char(string='Experience', required=True)

    categories = fields.Many2one('voca.teacher.categories',string='Category', required=True)

    language = fields.Selection([
            ('en', 'English'),
            ('ar', 'Arabic'),
        ], string="Language")
