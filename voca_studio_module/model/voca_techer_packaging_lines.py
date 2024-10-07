from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TeacherPackaging(models.Model):
    _name = 'voca.teacher.packaging.lines'
    # _description = 'Portal'

    name = fields.Char('Name', translate=True)

    package_id = fields.Many2one('voca.teacher', string='Teacher')

    available_time_slots_ids = fields.Many2many('voca.teacher.booking.lines',
                                                string='Time Slots',
                                               )

    quantity = fields.Float('Qty')

    order_line_ids = fields.One2many('sale.order', 'package_id', string='Sale Lines')






