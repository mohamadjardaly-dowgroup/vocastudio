# -*- coding: utf-8 -*-

from odoo import http, modules, tools , fields
from math import ceil
from werkzeug.urls import url_encode
from odoo.http import request
import logging
from datetime import datetime, timedelta
from odoo.addons.http_routing.models.ir_http import slug
import json

_logger = logging.getLogger(__name__)


class TeacherController(http.Controller):

    @http.route(['/'], type='http', auth="public",
                methods=['POST', 'GET'], website=True, csrf=False)
    def get_teacher_details_homepage(self, **kw):
        try:
            teacher = request.env['voca.teacher'].sudo().search([])
            # teacher = request.env['voca.teacher'].sudo().search([
            #     ('state', '=', 'approved'),
            #     ('show_on_teacher_page', '=', True),
            # ])
            categ = request.env['voca.teacher.categories'].sudo().search([])
            print("all teacher home :", teacher, kw)

            values = {
                'teachers': teacher,
                'categories': categ,
            }
            return request.render("website.homepage", values)
        except Exception as e:
            return e

    @http.route([
        '/teacher_profile',
        '/teacher_profile/page/<int:page>',
        '/teacher_profile/cat/<int:category_id>',
        '/teacher_profile/cat/<int:category_id>/page/<int:page>'
    ], type='http', auth="public", methods=['GET'], website=True, csrf=False)
    def get_teacher_details(self, category_id=None, page=1, **kw):
        try:
            per_page = 8  # Number of teachers per page

            # Apply category filtering before pagination
            teacher_domain = [('state', '=', 'approved')]

            # teacher_domain = [
            #     ('state', '=', 'approved'),
            #     ('show_on_teacher_page', '=', True),
            # ]
            
            if category_id:
                teacher_domain.append(('categories', 'in', [int(category_id)]))  # Fix category filtering

            # Count total teachers after filtering
            total_teachers = request.env['voca.teacher'].sudo().search_count(teacher_domain)

            # Odoo's built-in pager with URL including category
            pager = request.website.pager(
                url=f"/teacher_profile{'/cat/' + str(category_id) if category_id else ''}",
                total=total_teachers,
                page=page,
                step=per_page,
                url_args={},  # No need for ?page=x, handled in the route
                
            )

            # Fetch only paginated teachers **after filtering**
            teachers = request.env['voca.teacher'].sudo().search(
                teacher_domain,
                offset=pager['offset'],
                limit=per_page
            )

            # Fetch all categories
            categ = request.env['voca.teacher.categories'].sudo().search([])

            # Convert teacher data to JSON for easy use in the template
            teacher_data = [{
                'id': t.id,
                'name': t.name,
                'experience': t.experience,
                'instrument':t.instrument,
                'categories': [{'id': cat.id, 'name': cat.name} for cat in t.categories],
                'language': t.language,
                'lang': t.lang,
                'about': t.about or '',
                'image_url': f"/web/image/voca.teacher/{t.id}/image_1920",
            } for t in teachers]

            category_data = [{
                'id': cat.id,
                'name': cat.name,
                'image_url': f"/web/image/voca.teacher.categories/{cat.id}/image_1920"
            } for cat in categ]

            values = {
                'teachers': teacher_data,
                'categories': category_data,
                'pager': pager,  # Pass the pager object to the template
                'category_id': category_id,  # Maintain category selection
            }

            return request.render("voca_studio_module.teacher_profile_card", values)

        except Exception as e:
            return str(e)

    @http.route(['/teacher_profile/<int:teacher_id>'
                 ], type='http', auth="public",
                methods=['POST', 'GET'], website=True, csrf=False)
    def get_full_profile(self, teacher_id=None, category_id=None, **kw):
        print("tttttttttttttttt", teacher_id, category_id, **kw)

        teacher = request.env['voca.teacher'].sudo().browse(teacher_id)
        if not teacher.exists():
            return request.not_found()

        videos = teacher.attachment_video_ids

        return request.render('voca_studio_module.teacher_profile_template', {
            'teacher': teacher,
            'videos': videos,

        })

    @http.route(['/online-booking/<int:teacher_id>',
                 '/online-booking/package/<int:teacher_id>/<int:package_id>'], auth='public', website=True, csrf=True,
                methods=['GET'])
    def online_appointment(self, teacher_id=None, package_id=None, **kw):
        print("Package ------", package_id, teacher_id, kw)

        if request.env.user._is_public():
            return request.redirect('/web/login')

        teacher = request.env['voca.teacher'].sudo().browse(teacher_id)

        package_obj = teacher.packaging_ids.filtered(lambda x: x.id == package_id)
        if package_obj:
            request.session['package_id'] = {
                'id': package_obj.id,
                'price': package_obj.price,
                'quantity': package_obj.quantity,
                'name': package_obj.name,
            }
        if not teacher.exists():
            return request.not_found()

        bookings_by_day = {}

        for book in teacher.booking_ids:
            avail_date = book.availablity_date

            if isinstance(avail_date, str):
                avail_date = datetime.strptime(avail_date, '%Y-%m-%d %H:%M:%S')

            avail_date += timedelta(hours=3)
            day_with_date = avail_date.strftime('%A, %b %d/%Y')
            time = avail_date.strftime('%I:%M %p')
            if day_with_date not in bookings_by_day:
                bookings_by_day[day_with_date] = []
            bookings_by_day[day_with_date].append(time)

        print("bookings_by_day", bookings_by_day)
        teacher.product_id.website_url
        print("url ", teacher.product_id.website_url)
        # return request.render('voca_studio_module.available_days_list_with_times', {
        #     'teacher': teacher,
        #     'bookings_by_day': bookings_by_day,
        # })
        # product.website_url = "/shop/%s" % slug(product)

        return request.redirect(teacher.product_id.website_url)

    @http.route('/teacher_restriction_page', type='http', auth='public', website=True)
    def teacher_restriction_page(self, **kwargs):
        return request.render('voca_studio_module.teacher_login_restriction', {})

    @http.route('/get_booking_by_day', type='http', auth='public')
    def get_booking_by_day(self, teacher_id):
        print("teacher ", teacher_id)
        product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', int(teacher_id))], limit=1)
        teacher = request.env['voca.teacher'].sudo().search([('product_id', '=', product.id)])

        bookings_by_day = {}

        for book in teacher.booking_ids.filtered(lambda x: x.status == 'approved'):
            avail_date = book.availablity_date

            if isinstance(avail_date, str):
                avail_date = datetime.strptime(avail_date, '%Y-%m-%d %H:%M:%S')

            avail_date += timedelta(hours=3)
            day_with_date = avail_date.strftime('%A, %b %d/%Y')
            time = avail_date.strftime('%I:%M %p')
            if day_with_date not in bookings_by_day:
                bookings_by_day[day_with_date] = []
            bookings_by_day[day_with_date].append(time)
        print("booooooooking by day", bookings_by_day)

        return json.dumps(bookings_by_day)


class MasterClassController(http.Controller):

    @http.route(['/master_class/cat/'], type='http', auth="public",
                methods=['POST', 'GET'], website=True, csrf=False)
    def get_class_details(self, category_id=None, **kw):
        try:
            # teacher = request.env['master.classes'].sudo().search([])
            categ = request.env['master.classes.categories'].sudo().search([])
            # print("all teacher :", teacher, kw)
            print("nnnnnnnnnn")
            # teachers = request.env['voca.teacher'].sudo().search([('categories', '=', int(category_id))])
            return request.render('voca_studio_module.master_class_cat', {
                'categories': categ,  # Optionally pass the category for UI
            })
        except Exception as e:
            return e

    @http.route(['/master_class/cat/<int:category_id>'], type='http', auth="public",
                methods=['GET'], website=True, csrf=False)
    def get_class_cat_details(self, category_id=None, **kw):
        try:
            now_dt = fields.Datetime.now()

            # Read current pages from querystring, default to 1
            page_u = int(kw.get('page_u', 1))
            page_p = int(kw.get('page_p', 1))
            step_u = 12   # items per page (Upcoming)
            step_p = 12   # items per page (Past)
            offset_u = (page_u - 1) * step_u
            offset_p = (page_p - 1) * step_p

            # Domains
            upcoming_domain = [
                ('categories', '=', int(category_id)),
                ('lesson_state', '=', 'upcoming'),   
            ]
            past_domain = [
                ('categories', '=', int(category_id)),
                ('lesson_state', '=', 'completed'),
            ]

            # Counts
            total_u = request.env['master.classes'].sudo().search_count(upcoming_domain)
            total_p = request.env['master.classes'].sudo().search_count(past_domain)

            # Records (with limit/offset)
            upcoming_master = request.env['master.classes'].sudo().search(
                upcoming_domain, order="datetime_from ASC", limit=step_u, offset=offset_u
            )
            past_master = request.env['master.classes'].sudo().search(
                past_domain, order="datetime_from DESC", limit=step_p, offset=offset_p
            )

            base_url = f'/master_class/cat/{category_id}'

            # --- helper to build a pager dict that won't collide ---
            def build_pager(total, page, step, page_key, other_page_key, other_page_val, tab_name):
                page_count = max(1, ceil(total / float(step))) if step else 1

                def make_url(target_page):
                    args = {
                        page_key: target_page,
                        other_page_key: other_page_val,
                        'tab': tab_name,
                    }
                    return f"{base_url}?{url_encode(args)}#{'past-pane' if tab_name == 'past' else 'upcoming-pane'}"

                return {
                    'page': page,
                    'page_count': page_count,
                    'prev_url': make_url(max(1, page - 1)),
                    'next_url': make_url(min(page_count, page + 1)),
                    'pages': [{'num': i, 'url': make_url(i), 'current': (i == page)}
                              for i in range(1, page_count + 1)],
                }

            pager_u = build_pager(total_u, page_u, step_u, 'page_u', 'page_p', page_p, 'upcoming')
            pager_p = build_pager(total_p, page_p, step_p, 'page_p', 'page_u', page_u, 'past')

            return request.render('voca_studio_module.master_class_card_with_category', {
                'upcoming_master': upcoming_master,
                'past_master': past_master,
                'pager_u': pager_u,
                'pager_p': pager_p,
            })
        except Exception as e:
            return request.make_response("Error loading masterclasses: %s" % e)
    
    

    @http.route(['/master_profile/<int:master_id>'
                 ], type='http', auth="public",
                methods=['POST', 'GET'], website=True, csrf=False)
    def get_full_profile(self, master_id=None, **kw):
        print("mmmmmmm", master_id, **kw)

        master = request.env['master.classes'].sudo().browse(master_id)
        if not master.exists():
            return request.not_found()

        return request.render('voca_studio_module.master_profile_template', {
            'masters': master,

        })

    @http.route([
        '/booking/master/<int:master_id>',

    ], auth='public', website=True, csrf=True,
        methods=['GET'])
    def online_appointment(self, product_id=None, **kw):
        print("first ------", product_id, kw.get('master_id'))

        # product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', int(product_id))], limit=1)
        master_rec = request.env['master.classes'].sudo().browse(kw.get('master_id'))

        print("pppppp ------", master_rec, kw)

        if request.env.user._is_public():
            return request.redirect('/web/login')
        if product_id:

            # Fetch all master classes

            # Collect all individual dates between datetime_from and datetime_to for each class
            all_dates = []
            for master in master_rec.dates_ids.filtered(lambda x: x.status == 'draft'):
                if master.datetime_from and master.datetime_to:
                    start_date = master.datetime_from
                    end_date = master.datetime_to
                    # Generate dates between the start and end
                    current_date = start_date
                    while current_date <= end_date:
                        all_dates.append({
                            'master_id': master.id,
                            'name': master.name,
                            'date': current_date.strftime('%Y-%m-%d %H:%M:%S')
                        })
                        current_date += timedelta(days=1)

                print("all_dates", all_dates)
        master_rec.product_id.website_url
        return request.redirect(master_rec.product_id.website_url)

    @http.route([
        '/online-booking/master'

    ], auth='public', website=True, csrf=True,
        methods=['GET'])
    def online_appointment_ajax(self, product_id=None, **kw):
        print("first ajax ------", product_id, kw.get('master_id'))

        product = request.env['product.template'].sudo().search([('id', '=', int(product_id))], limit=1)
        master_rec = request.env['master.classes'].sudo().search([('product_id', '=', product.id)])

        print("newww ajax ------", master_rec, kw)

        if request.env.user._is_public():
            return request.redirect('/web/login')
        all_dates = []
        if product_id:
            for master in master_rec:
                # Filter dates with status 'draft' and map them directly
                draft_dates = master.dates_ids.filtered(lambda x: x.status == 'draft')
                for date_record in draft_dates:
                    all_dates.append({
                        'master_id': master.id,
                        'name': master.name,
                        'date': date_record.date.strftime('%Y-%m-%d %H:%M:%S')
                    })

        print("all_dates", all_dates)
        master_rec.product_id.website_url
        return request.make_response(
            json.dumps(all_dates),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/check_master_product', auth='public', website=True, csrf=True, methods=['GET'])
    def check_master_product(self, product_id=None, **kw):
        print("gggggggggggggggg",product_id)
        if not product_id:
            return request.make_response("Invalid product ID", headers=[('Content-Type', 'application/json')])

        # Check if the product is marked as master
        product = request.env['product.template'].sudo().search([('id', '=', int(product_id))], limit=1)

        is_master = product.is_master if product else False

        return request.make_response(json.dumps({'is_master': is_master}),
                                     headers=[('Content-Type', 'application/json')])
