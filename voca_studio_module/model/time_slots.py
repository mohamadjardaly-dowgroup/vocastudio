from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TimeSlots(models.Model):
    """
        Time slots model for managing different time slots for show.
    """
    _name = 'teacher.time.slots'
    _description = 'Time Slots'

    name = fields.Char(string='Time Slot', default='New',
                       readonly=True, help='Mention the name of the Time slots')
    teacher_time = fields.Char(string='Teacher Time', help='Mention the slot time')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "Name should be unique")
    ]

    @api.model
    def create(self, vals):
        """Supering create function to update name."""
        if vals['teacher_time']:
            vals['name'] = datetime.strptime(vals['teacher_time'], "%H:%M").strftime("%I:%M %p")
            vals['teacher_time'] = vals['teacher_time'].replace(":", ".")
        else:
            raise ValidationError('Please mention time!!')
        return super().create(vals)

    @api.model
    def write(self, vals):
        """Supering write function to update name."""
        if vals['movie_time']:
            vals['name'] = datetime.strptime(vals['teacher_time'],
                                             "%H:%M").strftime("%I:%M %p")
            vals['teacher_time'] = vals['teacher_time'].replace(":", ".")
        res = super(TimeSlots, self).write(vals)
        return res
