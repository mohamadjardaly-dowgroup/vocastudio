from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MasterClass(models.Model):
    _name = 'master.classes'
    _description = 'MasterClass'

    name = fields.Char(string='Subject', default='New')

    image_1920 = fields.Image(string="Image")

    date = fields.Date(string=_('Date'))

    time = fields.Char(string='Time')

    instructor = fields.Many2one('voca.teacher', string='Instructor')

    total_hours = fields.Float('Total Hours')

    lectures = fields.Integer(string="Lectures")

    categories = fields.Many2many('master.classes.categories', string='Category')


class MasterClassCategories(models.Model):
    _name = 'master.classes.categories'
    # _description = 'Portal'

    name = fields.Char('Title', required=True, translate=True)

    image_1920 = fields.Image(string="Image", readonly=False)  # image.mixin override
