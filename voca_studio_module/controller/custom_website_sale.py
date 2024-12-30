from datetime import datetime, timedelta
import json

import pytz
from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo import http
from odoo.http import request



class CustomWebsiteSale(WebsiteSale):
    @http.route(['/shop/<model("product.template"):product>'] ,type='http', auth="public", website=True)
    def product(self, product, **kwargs):
        # print("Package Inside the NEwwwwwww Controller CustomWebsite  >>>>>>>>>>>>>>>>", package)
        # product = package.product_id
        
        if product._name == 'product.product':
            product_template = product.product_tmpl_id
            # Now product_template is of type product.template
            print(f"This is a product.product. Parent product.template: {product_template.name}")
        elif product._name == 'product.template':
            product_template = product
            # product is already of type product.template
            print(f"This is a product.template: {product_template.name}")
        else:
            print("Unknown product type")
        
        
        category_id = product_template.categ_id.id if product_template.categ_id else None
        combination_info = product._get_combination_info(
            combination=None,
            add_qty=1,
            # pricelist=request.website.get_current_pricelist(),
            parent_combination=None,
            # pricelist=request.website.pricelist_id,

        )
      
        package_id = kwargs.get('package_id')
        # if product_template.product_variant_id.is_master and not package_id:
        #     master = request.env['master.classes'].search([('product_id', '=', product_template.product_variant_id.id)], limit=1)
        #     print( 'master.................................',master)
        #     if not master:
        #         return request.not_found()

        #     # Render the master class page
        #     return request.render('website_sale.product', {
        #         'product': product_template,
        #         'master': master,
        #         'dates': master.dates_ids,
        #         'category_id': category_id,
        #     })
      
        print("DEBUG: package_id =", package_id)  # Check if package_id is captured
        if package_id:
            package = request.env['voca.teacher.packaging.lines'].sudo().browse(int(package_id))
            if package.exists():
                teacher = package.package_id
                available_dates = teacher.available_time_slots_ids
                print("availablr datessssssssssssssssssssssssssssssssss",available_dates)
                

                teacher_time_slots = request.env['voca.teacher.booking.lines'].search([])
                print("Time slots in the system: ", len(teacher_time_slots))

                # Render the template with the package data
                return request.render('website_sale.product', {
                    'product': product_template,
                    'product_variant': product.product_variant_id,
                    'package': package,
                    'teacher' : teacher,
                    'available_dates': available_dates,
                    'product_price':package.price,
                    'combination_info': combination_info,
                    'category_id': category_id, 
                })
        else:
            return request.not_found() 
            
            
        return super(CustomWebsiteSale, self).product(product, **kwargs)
        
        
    @http.route('/available_dates', type='http', auth='public')
    def available_dates(self, teacher_id):
       
            print("Teacher ID: ", teacher_id)
            
            teacher = request.env['voca.teacher'].sudo().browse(int(teacher_id))
            
            bookings_by_day = {}

            for book in teacher.booking_ids.filtered(lambda x: x.status == 'approved'):
                avail_date = book.availablity_date

                if isinstance(avail_date, str):
                    avail_date = datetime.strptime(avail_date, '%Y-%m-%d %H:%M:%S')

                avail_date += timedelta(hours=2)  
                day_with_date = avail_date.strftime('%A, %b %d/%Y')
                time = avail_date.strftime('%I:%M %p')

                if day_with_date not in bookings_by_day:
                    bookings_by_day[day_with_date] = []
                bookings_by_day[day_with_date].append(time)

            print("Bookings by day: ", bookings_by_day)

            # Return the data as JSON
            return http.Response(
                json.dumps(bookings_by_day),
                content_type='application/json',
                status=200
            )
            
        

class CustomSaleOrder(http.Controller):

    @http.route(['/custom/update_sale_order_line'], type='http', auth="public", website=True, csrf=False)
    def update_sale_order_line(self, **kwargs):
        # Retrieve parameters from kwargs
        product_id = kwargs.get('product_id')
        print("Product ID /custom/update_sale_order_line:................................................ ", product_id)  
        selected_dates = kwargs.get('selected_dates')
        print("Selected Dates /custom/update_sale_order_line:................................................ ", selected_dates)
        package_id = kwargs.get('package_id')
        print("Package ID /custom/update_sale_order_line:................................................ ", package_id)
        if not product_id or not selected_dates:
            return request.make_response(
                json.dumps({"error": "Missing required parameters"}), 
                headers={'Content-Type': 'application/json'}
            )

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
        print("product: ", product)
        teacher = request.env['voca.teacher'].search([('product_id', '=', product.id)], limit=1)
        print("teacher: ", teacher.id)

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

        # Retrieve the package details
        package = request.env['voca.teacher.packaging.lines'].browse(int(package_id))
        print("package: ", package)

        # Add a sale order line with the product and the found booking lines
        # Search for an existing order line with the same product in the current sale order
        order_line = request.env['sale.order.line'].search([
            ('order_id', '=', sale_order.id),
            ('product_id', '=', product.id)
        ], limit=1)

        if order_line:
            # Update the existing order line
            order_line.write({
                'product_uom_qty': order_line.product_uom_qty + package.quantity-1, 
                'price_unit': package.price,  # Update price from the package
                'booking_ids': [(6, 0, booking_lines.ids)],  # Update booking lines
            })
            print("Updated order line:", order_line)
        else:
            # Create a new order line if none exists
            order_line = request.env['sale.order.line'].create({
                'order_id': sale_order.id,
                'product_id': product.id,
                'name': product.name,  # Set the name field
                'product_uom_qty': package.quantity-1,  # Default quantity
                'product_uom': product.uom_id.id,  # Unit of Measure
                'price_unit': package.price,  # Unit price from the package
                'tax_id': [(6, 0, product.taxes_id.ids)],  # Taxes
                'booking_ids': [(6, 0, booking_lines.ids)],  # Booking lines
            })
            print("Created new order line:", order_line)

        
        print('booking lines.............................',booking_lines)
        print('booking lines.ids.............................',booking_lines.ids)
        
        print("order_line:................... ", order_line)
        return request.redirect('/shop/cart')