from datetime import datetime, timedelta
import json

import pytz
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website.controllers.main import QueryURL
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError



class CustomWebsiteSale(WebsiteSale):
    @http.route(['/shop/<int:product_id>'] ,type='http', auth="public", website=True)
    def product(self, product_id, category='', search='', **kwargs):
        # print("Package Inside the NEwwwwwww Controller CustomWebsite  >>>>>>>>>>>>>>>>", package)
        # product = package.product_id
        print('Product_id .......... ',product_id)
        product_template = request.env['product.template'].sudo().browse(product_id)
        product=product_template
        print('Product fetched...........',product_template)
        if request.env.user._is_public():
            return request.redirect('/web/login')

        
        # if product._name == 'product.product':
        #     product_template = product.product_tmpl_id
        #     # Now product_template is of type product.template
        #     print(f"This is a product.product. Parent product.template: {product_template.name}")
        # elif product._name == 'product.template':
        #     product_template = product
        #     # product is already of type product.template
        #     print(f"This is a product.template: {product_template.name}")
        # else:
        #     print("Unknown product type")
        
        
        category_id = product_template.categ_id.id if product_template.categ_id else None
        combination_info = product._get_combination_info(
            combination=None,
            add_qty=1,
            # pricelist=request.website.get_current_pricelist(),
            parent_combination=None,
            # pricelist=request.website.pricelist_id,

        )
      
        package_id = kwargs.get('package_id')
        if product_template.product_variant_id.is_master and not package_id:
            master = request.env['master.classes'].sudo().search([('product_id', '=', product_template.product_variant_id.id)], limit=1)
            print( 'master.................................',master.id)
            if not master:
                return request.not_found()
            
            # dates = master.dates_ids.filtered(lambda d: d.status == 'draft')
            start_date=master.datetime_from
            end_date=master.datetime_to 
            # events = [
            #     {
            #         'title': master.name,
            #         'start':  start_date.strftime('%Y-%m-%d'),  # Start date
            #         'end': end_date.strftime('%Y-%m-%d'),  # End date (exclusive)
            #         }  # Unique identifier for the event
            #     # } for date in master.dates_ids if date.datetime_from and date.datetime_to
            # ]
            # Render the master class page
            
            if master.remaining_seats <= 0:
                booking_status = "All seats booked"
                can_book = False
            else:
                booking_status = f"{master.remaining_seats} seats available"
                can_book = True
            print("master.remaining_seats inside controller .....................",master.remaining_seats)
            keep = QueryURL(
                    '/shop',
                    **self._product_get_query_url_kwargs(
                        category=category and category.id,
                        search=search,
                        **kwargs,
                    ),
                )
            return request.render('website_sale.product', {
                'product': product_template,
                'master': master,
                'quantity':master.max_students,
                'booking_status':booking_status,
                'can_book':can_book,
                'remainingSeats': master.remaining_seats,
                'maxSeats': master.max_students,
                'starting_date':master.date.strftime('%d-%m-%Y'),
                'start_date': start_date.strftime('%H:%M:%S'),
                'end_date': end_date.strftime('%H:%M:%S'),
                'category_id': category_id,
                'keep': keep
            })
      
        print("DEBUG: package_id =", package_id)  # Check if package_id is captured
        if package_id:
            package = request.env['voca.teacher.packaging.lines'].sudo().browse(int(package_id))
            if package.exists():
                teacher = package.package_id
                available_dates = teacher.available_time_slots_ids
                print("availablr datessssssssssssssssssssssssssssssssss",available_dates)
                

                teacher_time_slots = request.env['voca.teacher.booking.lines'].sudo().search([])
                print("Time slots in the system: ", len(teacher_time_slots))
                keep = QueryURL(
                    '/shop',
                    **self._product_get_query_url_kwargs(
                        category=category and category.id,
                        search=search,
                        **kwargs,
                    ),
                )                
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
                    'keep': keep

                })
        else:
            return request.not_found() 
            
            
        return super(CustomWebsiteSale, self).product(product, **kwargs)
        
        
    @http.route('/available_dates', type='http', auth='public')
    def available_dates(self, teacher_id):
        print("Teacher ID: ", teacher_id)

        # Retrieve the user's time zone or default to UTC
        user_tz_name = request.env.user.tz or 'UTC'
        user_tz = pytz.timezone(user_tz_name)
        print(f"User's Time Zone: {user_tz}")

        teacher = request.env['voca.teacher'].sudo().browse(int(teacher_id))
        bookings_by_day = {}

        for book in teacher.booking_ids.filtered(lambda x: x.status in ['approved', 'booked']):
            avail_date = book.availablity_date

            if isinstance(avail_date, str):
                avail_date = datetime.strptime(avail_date, '%Y-%m-%d %H:%M:%S')

            # Assume avail_date is in UTC and convert to user's time zone
            avail_date = pytz.UTC.localize(avail_date).astimezone(user_tz)
            print("avail_date in hasan code : ", avail_date)

            # Format the date and time for the user's time zone
            day_with_date = avail_date.strftime('%A, %b %d/%Y')
            time = avail_date.strftime('%I:%M %p')

            if day_with_date not in bookings_by_day:
                bookings_by_day[day_with_date] = []

            # Include status for each time slot
            bookings_by_day[day_with_date].append({
                'time': time,
                'status': book.status  # Add the status (approved or booked)
            })

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
            
        user_tz_name = request.env.user.tz or 'UTC'
        print(f"User Time Zone Name: {user_tz_name}")
        
        user_tz = pytz.timezone(user_tz_name)
        print(f"User Time Zone: {user_tz}")
        
        # Parse selected dates
        dates = json.loads(selected_dates)
        print("Dates in /custom/update_sale_order_line:................................................ ", dates)
        parsed_dates = [
            datetime.strptime(date, '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            for date in dates
        ]
        print("Parsed Dates in my code : ", parsed_dates)
        
        # Retrieve the teacher associated with the product
        product = request.env['product.product'].sudo().browse(int(product_id))
        print("product: ", product)
        teacher = request.env['voca.teacher'].sudo().search([('product_id', '=', product.id)], limit=1)
        print("teacher: ", teacher.id)

        if not teacher:
            return {'error': 'No teacher found for the selected product'}
        
        # Get teacher availability and map UTC to user timezone
        teacher_availablity = teacher.booking_ids.mapped('availablity_date')
        print("teacher_availablity: ", teacher_availablity)
        
        availability_map = {}
        for utc_date in teacher_availablity:
            user_tz_date = utc_date.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S')
            availability_map[user_tz_date] = utc_date
        
        print("Availability Map (User TZ to UTC): ", availability_map)

        # Match selected dates in user timezone to UTC
        matching_utc_dates = [availability_map[date] for date in parsed_dates if date in availability_map]
        print("Matching UTC Dates: ", matching_utc_dates)

        # Use UTC dates to find matching booking lines
        booking_lines = request.env['voca.teacher.booking.lines'].sudo().search([
            ('availablity_date', 'in', matching_utc_dates),
            ('booking_id', '=', teacher.id)
        ])
        print("booking_lines found: ", booking_lines)

        # Retrieve the package details
        package = request.env['voca.teacher.packaging.lines'].sudo().browse(int(package_id))
        print("package: ", package)
        print("package.price: ", package.price)
        formatted_dates = '\n'.join(parsed_dates)

        print("package.name ...", package.name)
        description = f"{package.name}\nSelected Dates: {formatted_dates}\n"
        print(('product_id.............', product.id))
        
        # Create or update the sale order and its lines
        sale_order = request.website.sale_get_order()
        if not sale_order:
            partner_id = request.env.user.partner_id.id
            sale_order = request.env['sale.order'].sudo().create({
                'partner_id': partner_id,
                'website_id': request.website.id,
            })

        order_line = request.env['sale.order.line'].sudo().search([
            ('order_id', '=', sale_order.id),
            ('product_id', '=', product.id)
        ], limit=1)

        if order_line:
            order_line.sudo().write({
                'product_uom_qty': package.quantity,
                'price_unit': package.price / package.quantity,
                'name': description,
                'package_id': package.id,
                'booking_ids': [(6, 0, booking_lines.ids)],
            })
        else:
            sale_order.sudo().write({'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': package.quantity,
                'price_unit': package.price / package.quantity,
                'name': description,
                'package_id': package.id,
                'product_uom': product.uom_id.id,
                'tax_id': [(6, 0, product.taxes_id.ids)],
                'booking_ids': [(6, 0, booking_lines.ids)],
            })]})
            print("Created new order line:", order_line)
        
        print("booking lines.............................", booking_lines)
        print("booking lines.ids.............................", booking_lines.ids)

        
        return request.redirect('/shop/cart')

  
   
