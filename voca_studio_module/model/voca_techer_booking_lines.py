from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TeacherTags(models.Model):
    _name = 'voca.teacher.booking.lines'
    # _description = 'Portal'

    name = fields.Char('Name', required=True, translate=True)

    booking_id = fields.Many2one('voca.teacher', string='Teacher')

    availablity_date = fields.Datetime('Date')

    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
        ], string='Status', index=True, readonly=True, copy=False,
        default='draft', tracking=True)


    def action_approved(self):
        for rec in self:
            rec.status = 'approved'
    def action_refused(self):
        for rec in self:
            rec.status = 'refused'