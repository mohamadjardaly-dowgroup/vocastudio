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
    price = fields.Monetary('Price', currency_field="currency_id", required=True,store=True,readonly=False)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    
    discount=fields.Float('Discount (%)', digits='Discount', default=0.0)
    total = fields.Monetary('Total', currency_field="currency_id", compute='_compute_total', store=True)
    
    package_time = fields.Char(string='Time')

    order_line_ids = fields.One2many('sale.order', 'package_id', string='Sale Lines')
    product_id = fields.Many2one('product.product', string='Product',related="package_id.product_id", readonly=True)
    
    @api.depends('price', 'discount')
    def _compute_total(self):
        for record in self:
            record.total = record.price *  (1 - (record.discount or 0.0) / 100)
            print("record.total ...........", record.total)









