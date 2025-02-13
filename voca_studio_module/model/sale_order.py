# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.http import request
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
                        booking_id.write({'status': 'booked','lesson_state': 'upcoming'})
                        print("the status of booking id is ...............",booking_id.status)
                        
                elif line.booking_master_ids :
                    print("I am inside if booking_master_ids ////////")
                    for booking_master_id in line.booking_master_ids:
                        print('Updating Booking ID:', booking_master_id.id)
                        booking_master_id.write({'status': 'booked'})
                        print("the status of booking id is ...............",booking_master_id.status)
             # Update remaining seats for master class
                if line.product_id.is_master:
                    master_class = line.product_id.master_class_id
                    print("Master Class:...........", master_class)
                    if master_class:
                        total_seats_needed = line.product_uom_qty
                        print("Total Seats Needed:...........", total_seats_needed)
                        if master_class.remaining_seats < total_seats_needed:
                            print("Master Class Remaining Seats:...........", master_class.remaining_seats)
                            raise ValidationError(_("Not enough seats available for the master class."))
                        master_class.remaining_seats -= total_seats_needed
                        print("Master Class Remaining Seats after booking:...........", master_class.remaining_seats)
            # Find the teacher linked to the lesson (product)
                teacher_packaging_line = self.env['voca.teacher.packaging.lines'].search(
                    [('product_id', '=', line.product_id.id)], limit=1
                )
                print("Teacher Packaging Line:...........", teacher_packaging_line)
                if teacher_packaging_line:
                    teacher = teacher_packaging_line.package_id  # Get the related teacher
                    print("Teacher related to the package :...........", teacher)
                    if teacher and teacher.instructor and teacher.instructor.email:
                        # Send email to teacher
                        self._send_teacher_email(teacher.instructor, line)
        return res
    def _send_teacher_email(self, teacher, sale_order_line):
        """ Sends an email to the teacher when a student books a lesson. """
        print("Sending email to teacher:", teacher.email)

        email_template = self.env.ref('voca_studio_module.mail_template_lesson_booking_teacher')  # Replace with your actual email template XML ID
        if email_template:
            email_template.sudo().send_mail(teacher.id, force_send=True)
            print("Email sent to:", teacher.email)
            
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
            # if line.package_id:
            #     print("I am inside if line.package_id", line.package_id)
            #     # Use the price from the package
            #     line.price_unit = line.package_id.price
            #     line.product_uom_qty = line.package_id.quantity
            
            if line.package_id:
                # Use the package price directly for the subtotal
                print("line.price_unit............",line.price_unit)
                line.product_uom_qty = line.package_id.quantity
                line.price_unit = line.package_id.price / line.product_uom_qty
                print("line.price_unit after division............",line.price_unit)
                
                
                # line.price_total = line.price_subtotal
            else:
            
            # if line.product_id.is_master:
            #     # Use the price from the master class
            #     line.price_unit = line.product_id.seat_price
            #     continue

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
    
