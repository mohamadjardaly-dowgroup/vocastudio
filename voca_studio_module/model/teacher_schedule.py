from odoo import models, fields, api
from datetime import datetime, timedelta
import pytz


class VocaTeacherSchedule(models.Model):
    _name = 'voca.teacher.schedule'
    _description = "Teacher Weekly Schedule"

    teacher_id = fields.Many2one('voca.teacher', required=True)
    weekday = fields.Selection([
        ('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'),
        ('3', 'Thursday'), ('4', 'Friday'), ('5', 'Saturday'), ('6', 'Sunday')
    ], string='Day of Week', required=True)
    time_from = fields.Float(string='From (24h, utc)', required=True)
    time_to = fields.Float(string='To (24h, utc)', required=True)

    
