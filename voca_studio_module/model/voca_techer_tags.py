from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TeacherTags(models.Model):
    _name = 'voca.teacher.tags'
    # _description = 'Portal'

    name = fields.Char('Name', required=True, translate=True)

