import json
from odoo import http
from odoo.http import request
from datetime import datetime
import pytz

class BookingController(http.Controller):
    @http.route('/submit_booking', type='http', auth='public', website=True)
    def submit_booking(self, product_id, selected_dates, **kwargs):
        print("submit_booking:......................... ", product_id, selected_dates)
        
        # Parse the selected dates JSON string
        dates = json.loads(selected_dates)
        parsed_dates = []
        
        for date in dates:
            # Parse the date string to a datetime object in UTC
            date_utc = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=None)
            print("date (UTC):......................... ", date_utc)
            parsed_dates.append(date_utc)

        # Create or find the current sale order (cart)
        sale_order = request.website.sale_get_order()
        sale_order = request.env['sale.order'].search([('website_id', '=', request.website.id), ('state', '=', 'draft')], limit=1)
        print("sale_order in my booking controller .............: ", sale_order)
        if not sale_order:
            # Create a new sale order if one doesn't exist
            sale_order = request.env['sale.order'].create({
                'partner_id': request.env.user.partner_id.id,  # Associate with current user (or session)
                'website_id': request.website.id,
            })
        print("sale_order after creating a one if it doesn t exist .............: ", sale_order)

        # Retrieve the teacher associated with the product
        product = request.env['product.product'].browse(int(product_id))
        teacher = request.env['voca.teacher'].search([('product_id', '=', product.id)], limit=1)
        print("teacher: ", teacher)

        if not teacher:
            return {'error': 'No teacher found for the selected product'}
        
        # Get the availability dates of the teacher
        teacher_availablity = teacher.booking_ids.mapped('availablity_date')
        print("teacher_availablity: ", teacher_availablity)

        # Convert teacher availability dates to UTC for comparison
        teacher_availablity_utc = [date.astimezone(pytz.UTC) for date in teacher_availablity]
        print("teacher_availablity_utc: ", teacher_availablity_utc)

        # Convert teacher availability dates to a set of strings for easier comparison
        teacher_availablity_str = set([date.strftime('%Y-%m-%d %H:%M:%S') for date in teacher_availablity_utc])
        print("teacher_availablity_str: ", teacher_availablity_str)

        # Filter parsed dates to only include those that match the teacher's availability
        matching_dates = [date for date in parsed_dates if date.strftime('%Y-%m-%d %H:%M:%S') in teacher_availablity_str]
        print("matching_dates: ", matching_dates)

        # Search for existing booking lines based on the matching dates and the teacher
        booking_lines = request.env['voca.teacher.booking.lines'].search([
            ('availablity_date', 'in', matching_dates),
            ('booking_id', '=', teacher.id)
        ])
        print("booking_lines found: ", booking_lines)
        
        
        
        
        # Add a sale order line with the product and the found booking lines
        order_line = request.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': product.id,
            'booking_ids': [(6, 0, booking_lines.ids)],  # Use (6, 0, [ids]) to link existing records
        })
        print("order_line:................... ", order_line)
        return request.redirect('/shop/cart')