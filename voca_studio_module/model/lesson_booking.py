from odoo import models, fields

class LessonBooking(models.Model):
    _name = 'lesson.booking'
    _description = 'Lesson Booking'

    student_id = fields.Many2one('res.partner', string='Student', required=True)
    teacher_id = fields.Many2one('voca.teacher', string='Teacher', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    date = fields.Datetime('Date', required=True)
    state = fields.Selection([
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled')
    ], string='Status', default='upcoming', required=True)
