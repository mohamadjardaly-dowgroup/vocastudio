from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TeacherCategories(models.Model):
    _name = 'voca.teacher.categories'
    # _description = 'Portal'

    name = fields.Char('Title', required=True, translate=True)



