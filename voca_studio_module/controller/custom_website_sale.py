from datetime import datetime, timedelta
import json

import pytz
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website.controllers.main import QueryURL
from math import ceil
from odoo import fields, http
from odoo.http import request
from odoo.exceptions import UserError
from odoo.tools import format_amount
import logging
_logger = logging.getLogger(__name__)

class CustomWebsiteSale(WebsiteSale):
    @http.route(['/shop/<int:product_id>'] ,type='http', auth="public", website=True)
    def product(self, product_id, category='', search='', **kwargs):
        # print("Package Inside the NEwwwwwww Controller CustomWebsite  >>>>>>>>>>>>>>>>", package)
        # product = package.product_id
        print('Product_id .......... ',product_id)
        product_template = request.env['product.template'].sudo().browse(product_id)
        product=product_template
        print('Product fetched...........',product_template)
        if not product_template.product_variant_id.is_master:
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

            # Convert timezone
            user_tz_name = request.env.user.tz or 'UTC'  # Get user timezone
            user_tz = pytz.timezone(user_tz_name)
            server_tz = pytz.UTC  

            start_date = master.datetime_from
            end_date = master.datetime_to

            # Convert datetime from server time (UTC) to user timezone
            if start_date:
                start_date = server_tz.localize(start_date).astimezone(user_tz)
            if end_date:
                end_date = server_tz.localize(end_date).astimezone(user_tz)
            
            # dates = master.dates_ids.filtered(lambda d: d.status == 'draft')
            
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
            pricelist = request.website._get_current_pricelist()

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
                'keep': keep,
                'pricelist': pricelist,
                'currency_id': pricelist.currency_id,
                'currency': pricelist.currency_id,
                'format_amount': lambda amount, currency: format_amount(request.env, amount, currency),
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
                
                pricelist = request.website._get_current_pricelist()
                _logger.info("DEBUG: Pricelist Currency Name: %s (ID: %s)", pricelist.currency_id.name, pricelist.currency_id.id)
                _logger.info("DEBUG: Package Currency Name: %s (ID: %s)", package.currency_id.name, package.currency_id.id)
                _logger.info("DEBUG: Pricelist Currency Rate: %s", pricelist.currency_id.rate)
                _logger.info("DEBUG: Package Currency Rate: %s", package.currency_id.rate)
                # computed_price = pricelist._get_product_price(package.product_id, 1.0, request.env.user.partner_id)
                package_currency = package.currency_id
                package_price = package.total

                if package_currency != pricelist.currency_id:
                    converted_price = package_currency._convert(
                        from_amount=package_price,
                        to_currency=pricelist.currency_id,
                        company=request.env.company,
                        date=fields.Date.today()
                    )
                    # print("Converted Price..........: ", converted_price)
                else:
                    converted_price = package_price

                # Render the template with the package data
                return request.render('website_sale.product', {
                    'product': product_template,
                    'product_variant': product.product_variant_id,
                    'package': package,
                    'teacher' : teacher,
                    'available_dates': available_dates,
                    'product_price': converted_price,
                    'combination_info': combination_info,
                    'category_id': category_id, 
                    'keep': keep,
                    'format_amount': lambda amount, currency: format_amount(request.env, amount, currency),
                    'currency_id': pricelist.currency_id,
                })
        else:
            return request.not_found() 
            
            
        return super(CustomWebsiteSale, self).product(product, **kwargs)

    @http.route('/available_dates', type='http', auth='public')
    def available_dates(self, teacher_id, date=None):
        print("Teacher ID: ", teacher_id)
        print("Requested Date: ", date)  # Debugging log

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
            print("Converted Availability Date: ", avail_date)

            # Format the date for the frontend request format (YYYY-MM-DD)
            day_with_date = avail_date.strftime('%Y-%m-%d')
            time = avail_date.strftime('%I:%M %p')

            if day_with_date not in bookings_by_day:
                bookings_by_day[day_with_date] = []

            # Include status for each time slot
            bookings_by_day[day_with_date].append({
                'time': time,
                'status': book.status  # Add the status (approved or booked)
            })

        print("Bookings by day: ", bookings_by_day)

        # If a specific date is requested, return only that date's slots
        if date:
            return http.Response(
                json.dumps(bookings_by_day.get(date, [])),  # Return only matching date's data
                content_type='application/json',
                status=200
            )

        # Otherwise, return all available dates
        return http.Response(
            json.dumps(bookings_by_day),
            content_type='application/json',
            status=200
        )
        
    @http.route('/available_times', type='http', auth='public')
    def available_times(self, teacher_id, date):
        print("Fetching times for...........:", teacher_id, date)

        user_tz_name = request.env.user.tz or 'UTC'
        user_tz = pytz.timezone(user_tz_name)

        teacher = request.env['voca.teacher'].sudo().browse(int(teacher_id))
        time_slots = []

        for book in teacher.booking_ids.filtered(lambda x: x.status in ['approved', 'booked']):
            avail_date = book.availablity_date

            if isinstance(avail_date, str):
                avail_date = datetime.strptime(avail_date, '%Y-%m-%d %H:%M:%S')

            avail_date = pytz.UTC.localize(avail_date).astimezone(user_tz)

            # Match the date requested
            if avail_date.strftime('%Y-%m-%d') != date:
                continue

            time_str = avail_date.strftime('%I:%M %p')  # e.g., "09:00 AM"
            time_slots.append({
                'time': time_str,
                'status': book.status
            })

        # ✅ Sort the time slots chronologically using parsed datetime objects
        time_slots.sort(key=lambda x: datetime.strptime(x['time'], '%I:%M %p'))

        print(f"Sorted time slots for......... {date}: {time_slots}")

        return http.Response(
            json.dumps(time_slots),
            content_type='application/json',
            status=200
        )

    # @http.route('/available_dates', type='http', auth='public')
    # def available_dates(self, teacher_id):
    #     print("Teacher ID: ", teacher_id)

    #     # Retrieve the user's time zone or default to UTC
    #     user_tz_name = request.env.user.tz or 'UTC'
    #     user_tz = pytz.timezone(user_tz_name)
    #     print(f"User's Time Zone: {user_tz}")

    #     teacher = request.env['voca.teacher'].sudo().browse(int(teacher_id))
    #     bookings_by_day = {}

    #     for book in teacher.booking_ids.filtered(lambda x: x.status in ['approved', 'booked']):
    #         avail_date = book.availablity_date

    #         if isinstance(avail_date, str):
    #             avail_date = datetime.strptime(avail_date, '%Y-%m-%d %H:%M:%S')

    #         # Assume avail_date is in UTC and convert to user's time zone
    #         avail_date = pytz.UTC.localize(avail_date).astimezone(user_tz)
    #         print("avail_date in hasan code : ", avail_date)

    #         # Format the date and time for the user's time zone
    #         day_with_date = avail_date.strftime('%A, %b %d/%Y')
    #         time = avail_date.strftime('%I:%M %p')

    #         if day_with_date not in bookings_by_day:
    #             bookings_by_day[day_with_date] = []

    #         # Include status for each time slot
    #         bookings_by_day[day_with_date].append({
    #             'time': time,
    #             'status': book.status  # Add the status (approved or booked)
    #         })

    #     print("Bookings by day: ", bookings_by_day)

    #     # Return the data as JSON
    #     return http.Response(
    #         json.dumps(bookings_by_day),
    #         content_type='application/json',
    #         status=200
    #     )
    

            
        

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

        pricelist = request.website._get_current_pricelist()
        print("Pricelist in sale order ................: ", pricelist)
        # Fetch the package's price and currency
        package_currency = package.currency_id
        package_price = package.total
        print("Package Price in sale order ...: ", package_price)
        
        
        # Convert package price to the selected pricelist's currency
        if package_currency != pricelist.currency_id:
            converted_price = package_currency._convert(
                from_amount=package_price,
                to_currency=pricelist.currency_id,
                company=request.env.company,
                date=fields.Date.today()
            )
            print("Converted Price in sale order ..........: ", converted_price)
        else:
            converted_price = package_price  # No conversion needed if the currencies match
            print("Converted Price inside else in sale order  ..........: ", converted_price)

        if order_line:
            order_line.sudo().write({
                'product_uom_qty': package.quantity,
                'converted_price': converted_price,
                'price_unit': converted_price  / package.quantity,
                'name': description,
                'package_id': package.id,
                'booking_ids': [(6, 0, booking_lines.ids)],
            })
        else:
            sale_order.sudo().write({'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': package.quantity,
                'converted_price': converted_price,
                'price_unit': converted_price  / package.quantity,
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

class StudentDashboard(http.Controller):

    @http.route('/my_dashboard', type='http', auth="public", website=True)
    def my_dashboard(self, **kwargs):
        # Render the main dashboard template
        return request.render('voca_studio_module.my_dashboard_template')

    @http.route('/my_dashboard/upcoming-lessons', type='http', auth="public", website=True)
    def my_upcoming_lessons(self, page=1, limit=12, **kwargs):
        try:
            page = int(page)
        except ValueError:
            page = 1

        student = request.env.user.partner_id

        # Fetch all order lines for the student
        order_lines = request.env['sale.order.line'].sudo().search([
            ('order_id.partner_id', '=', student.id)
        ])

        # Filter upcoming bookings
        # upcoming_bookings = request.env['voca.teacher.booking.lines'].sudo().search([
        #     ('booking_order_id', 'in', order_lines.ids),
        #     ('lesson_state', '=', 'upcoming')
        # ])
        
        upcoming_bookings = request.env['voca.teacher.booking.lines'].sudo().search([
            ('booking_order_id', 'in', order_lines.ids),
            ('lesson_state', '=', 'upcoming'),
            '|',
            ('booking_type', '=', False),
            ('booking_type', '=', 'private_lesson'),
        ], order='availablity_date ASC')

        # Pagination logic
        offset = (page - 1) * limit
        total_upcoming = len(upcoming_bookings)
        total_pages = ceil(total_upcoming / limit)
        upcoming_bookings = upcoming_bookings[offset:offset + limit]

        return request.render('voca_studio_module.upcoming_lessons_partial', {
            'upcoming_bookings': upcoming_bookings,
            'page': page,
            'total_pages': total_pages,
        })

    @http.route('/my_dashboard/upcoming-masters', type='http', auth="user", website=True)
    def my_upcoming_masters(self, page=1, limit=25, **kwargs):
        try:
            page = int(page)
        except ValueError:
            page = 1

        student = request.env.user.partner_id

        # Fetch upcoming master classes booked by the student
        order_lines = request.env['sale.order.line'].sudo().search([
            ('order_id.partner_id', '=', student.id),
            ('order_id.state', '=', 'sale'),
            ('product_id.is_master', '=', True),
            ('product_id.master_class_id.lesson_state', '=', 'upcoming')
        ])

        user_tz_name = request.env.user.tz or 'UTC'  # Get the user's timezone
        user_tz = pytz.timezone(user_tz_name)
        server_tz = pytz.UTC  # Odoo stores datetime in UTC

        master_class_data = []
        for line in order_lines:
            master_class = line.product_id.master_class_id
            if master_class:
                # Convert the times from UTC to the user's timezone
                start_date = master_class.datetime_from
                end_date = master_class.datetime_to

                if start_date:
                    start_date = server_tz.localize(start_date).astimezone(user_tz)
                if end_date:
                    end_date = server_tz.localize(end_date).astimezone(user_tz)

                master_class_data.append({
                    'master_class': master_class,
                    'start_time': start_date ,
                    'end_time': end_date ,
                    'seats_booked': line.product_uom_qty,
                })

        # Pagination logic
        total_masters = len(master_class_data)
        total_pages = (total_masters + limit - 1) // limit  # Simple ceil division
        offset = (page - 1) * limit
        paginated_masters = master_class_data[offset:offset + limit]

        return request.render('voca_studio_module.upcoming_masters_partial', {
            'upcoming_masters': paginated_masters,
            'page': page,
            'total_pages': total_pages,
            'limit': limit,
        })
    
    @http.route('/my_dashboard/completed-lessons', type='http', auth="user", website=True)
    def my_completed_lessons(self, page=1, limit=10, **kwargs):
        try:
            page = int(page)
        except ValueError:
            page = 1

        student = request.env.user.partner_id

        # Fetch all order lines for the student
        order_lines = request.env['sale.order.line'].sudo().search([
            ('order_id.partner_id', '=', student.id),
            ('order_id.state', '=', 'sale')  # Ensure order is confirmed
        ])

        # Fetch completed lesson bookings (normal lessons)
        completed_bookings = request.env['voca.teacher.booking.lines'].sudo().search([
            ('booking_order_id', 'in', order_lines.ids),
            ('lesson_state', '=', 'completed')
        ])

         # Fetch completed master classes (Ensuring uniqueness with a set)
        completed_master_classes = request.env['sale.order.line'].sudo().search([
            ('order_id.partner_id', '=', student.id),
            ('order_id.state', '=', 'sale'),  # Only confirmed orders
            ('product_id.is_master', '=', True),
            ('product_id.master_class_id.lesson_state', '=', 'completed')
        ])

        # Use a set to store unique master class IDs
        unique_master_classes = set()
        master_class_objects = []

        for line in completed_master_classes:
            master_class = line.product_id.master_class_id
            if master_class and master_class.id not in unique_master_classes:
                unique_master_classes.add(master_class.id)
                master_class_objects.append(master_class)

        # Combine normal lessons and master classes
        all_completed = list(completed_bookings) + master_class_objects

        # Pagination logic
        offset = (page - 1) * limit
        total_completed = len(all_completed)
        total_pages = ceil(total_completed / limit)
        paginated_completed = all_completed[offset:offset + limit]

        return request.render('voca_studio_module.completed_lessons_partial', {
            'completed_bookings': paginated_completed,
            'page': page,
            'total_pages': total_pages,
        })


class TeacherDashboard(http.Controller):
    print("Teacher Dashboard Controller")
    @http.route('/teacher_dashboard', type='http', auth="user", website=True)
    def teacher_dashboard(self, **kwargs):
        """Render the Teacher Dashboard"""
        return request.render('voca_studio_module.teacher_dashboard_template')

    @http.route('/teacher_dashboard/upcoming-lessons', type='http', auth="user", website=True)
    def teacher_upcoming_lessons(self, page=1, limit=25, **kwargs):
        try:
            page = int(page)
        except ValueError:
            page = 1

        teacher = request.env.user.partner_id

        # Fetch upcoming lessons for the teacher (sorted by date)
        upcoming_lessons = request.env['voca.teacher.booking.lines'].sudo().search([
            ('booking_id', '=', teacher.teacher_id.id),
            ('lesson_state', '=', 'upcoming'),
            '|',
            ('booking_type', '=', False),
            ('booking_type', '=', 'private_lesson'),
        ], order='availablity_date ASC')

        # Pagination logic
        offset = (page - 1) * limit
        total_lessons = len(upcoming_lessons)
        total_pages = ceil(total_lessons / limit)
        paginated_lessons = upcoming_lessons[offset:offset + limit]

        return request.render('voca_studio_module.teacher_upcoming_lessons_partial', {
            'upcoming_lessons': paginated_lessons,
            'page': page,
            'total_pages': total_pages,
        })

    @http.route('/teacher_dashboard/completed-lessons', type='http', auth="user", website=True)
    def teacher_completed_lessons(self, page=1, limit=10, **kwargs):
        try:
            page = int(page)
        except ValueError:
            page = 1

        teacher = request.env.user.partner_id

        # Fetch completed one-on-one lessons
        completed_lessons = request.env['voca.teacher.booking.lines'].sudo().search([
            ('booking_id', '=', teacher.teacher_id.id),
            ('lesson_state', '=', 'completed')
        ], order='availablity_date DESC')

        # Fetch completed master classes where the teacher is the instructor
        completed_master_classes = request.env['master.classes'].sudo().search([
            ('instructor', '=', teacher.teacher_id.id),
            ('lesson_state', '=', 'completed')
        ], order='datetime_from DESC')

        # Combine both completed one-on-one lessons and master classes
        all_completed = list(completed_lessons) + list(completed_master_classes)
        print("all_completed: ", all_completed)
        # Pagination logic
        offset = (page - 1) * limit
        total_completed = len(all_completed)
        total_pages = ceil(total_completed / limit)
        paginated_completed = all_completed[offset:offset + limit]

        return request.render('voca_studio_module.teacher_completed_lessons_partial', {
            'completed_lessons': paginated_completed,
            'page': page,
            'total_pages': total_pages,
        })


    @http.route('/teacher_dashboard/master-classes', type='http', auth="user", website=True)
    def teacher_master_classes(self, page=1, limit=25, **kwargs):
        try:
            page = int(page)
        except ValueError:
            page = 1

        teacher = request.env.user.partner_id

        # Fetch master classes where the teacher is the instructor
        master_classes = request.env['master.classes'].sudo().search([
            ('instructor', '=', teacher.teacher_id.id),
            ('lesson_state', '=', 'upcoming')
        ])

        user_tz_name = request.env.user.tz or 'UTC'  # Get the teacher's timezone
        user_tz = pytz.timezone(user_tz_name)
        server_tz = pytz.UTC  # Odoo stores datetime in UTC

        master_class_data = []
        for master_class in master_classes:
            # Convert the times from UTC to the user's timezone
            start_date = master_class.datetime_from
            end_date = master_class.datetime_to

            if start_date:
                start_date = server_tz.localize(start_date).astimezone(user_tz)
            if end_date:
                end_date = server_tz.localize(end_date).astimezone(user_tz)

            master_class_data.append({
                'master_class': master_class,
                'start_time': start_date,
                'end_time': end_date,
                'remaining_seats': master_class.remaining_seats,
            })

        # Pagination logic
        total_master_classes = len(master_class_data)
        total_pages = (total_master_classes + limit - 1) // limit  # Simple ceil division
        offset = (page - 1) * limit
        paginated_master_classes = master_class_data[offset:offset + limit]

        return request.render('voca_studio_module.teacher_master_classes_partial', {
            'master_classes': paginated_master_classes,
            'page': page,
            'total_pages': total_pages,
            'limit': limit,
        })
        
        
        
    @http.route('/teacher_dashboard/mark_lesson_completed', type='http', auth="user", methods=['POST'])
    def mark_lesson_completed(self, **kwargs):
        """Marks a one-on-one lesson as completed"""
        lesson_id = kwargs.get('lesson_id')
        
        if not lesson_id:
            return request.redirect('/teacher_dashboard?error=Lesson ID not provided')

        lesson = request.env['voca.teacher.booking.lines'].sudo().browse(int(lesson_id))
        if lesson.exists() and lesson.lesson_state == 'upcoming':
            lesson.write({'lesson_state': 'completed'})
        
        return request.redirect('/teacher_dashboard')

    @http.route('/teacher_dashboard/mark_masterclass_completed', type='http', auth="user", methods=['POST'])
    def mark_masterclass_completed(self, **kwargs):
        """Marks a master class as completed"""
        masterclass_id = kwargs.get('masterclass_id')

        if not masterclass_id:
            return request.redirect('/teacher_dashboard?error=Master Class ID not provided')

        master_class = request.env['master.classes'].sudo().browse(int(masterclass_id))
        if master_class.exists() and master_class.lesson_state == 'upcoming':
            master_class.write({'lesson_state': 'completed'})

        return request.redirect('/teacher_dashboard')

 

   
    
    


  
   
