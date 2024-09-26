from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Teacher(models.Model):
    _name = 'voca.teacher.slots'

    availablity_date = fields.Date('Date')
    availablity_date_time = fields.Datetime('Date time', default=lambda self: fields.Datetime.now())

    slot_id  = fields.Many2one('voca.teacher',string='Slot')


