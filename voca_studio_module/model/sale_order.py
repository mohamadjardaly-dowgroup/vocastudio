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
    
    #samiha##########################################################   
    package_id = fields.Many2one('voca.teacher.packaging.lines', string='Package')
    
    @api.depends('product_id', 'product_uom', 'product_uom_qty', 'package_id')
    def _compute_price_unit(self):
        for line in self:
            # Check if a package is associated with the order line
            if line.package_id:
                print("I am inside if line.package_id", line.package_id)
                # Use the price from the package
                line.price_unit = line.package_id.price
                continue

            # Default behavior for other cases
            if line.qty_invoiced > 0 or (line.product_id.expense_policy == 'cost' and line.is_expense):
                continue
            if not line.product_uom or not line.product_id:
                line.price_unit = 0.0
            else:
                line = line.with_company(line.company_id)
                price = line._get_display_price()
                line.price_unit = line.product_id._get_tax_included_unit_price_from_price(
                    price,
                    line.currency_id or line.order_id.currency_id,
                    product_taxes=line.product_id.taxes_id.filtered(
                        lambda tax: tax.company_id == line.env.company
                    ),
                    fiscal_position=line.order_id.fiscal_position_id,
                )

