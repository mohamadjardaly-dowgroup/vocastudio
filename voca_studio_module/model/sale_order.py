# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.osv import expression

from odoo.addons.http_routing.models.ir_http import unslug


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    package_id = fields.Many2one('voca.teacher.packaging.lines',string='Teacher package')
    
    #samiha##########################################################
    def action_confirm(self):
        print("Sale Order Confirmed: ...................", self.name)
        res = super(SaleOrder, self).action_confirm()
        
        for order in self:
            for line in order.order_line:
                if line.booking_ids:
                    print("I am inside if line.booking ids ////////")
                    for booking_id in line.booking_ids:
                        print('Updating Booking ID:', booking_id.id)
                        booking_id.write({'status': 'booked'})
                        print("the status of booking id is ...............",booking_id.status)
                        
                elif line.booking_master_ids :
                    print("I am inside if booking_master_ids ////////")
                    for booking_master_id in line.booking_master_ids:
                        print('Updating Booking ID:', booking_master_id.id)
                        booking_master_id.write({'status': 'booked'})
                        print("the status of booking id is ...............",booking_master_id.status)
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    booking_ids= fields.One2many('voca.teacher.booking.lines', 'booking_order_id', string='Booking')
    booking_master_ids= fields.One2many('master.class.date', 'booking_order_id', string='Booking master')

