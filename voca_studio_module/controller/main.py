# -*- coding: utf-8 -*-

from odoo import http, modules, tools
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
            categ = request.env['voca.teacher.categories'].sudo().search([])
            print("all teacher home :", teacher, kw)

            values = {
                'teachers': teacher,
                'categories': categ,
            }
            return request.render("website.homepage", values)
        except Exception as e:
            return e

    @http.route(['/teacher_profile',
                 '/teacher_profile/cat/<int:category_id>'], type='http', auth="public",
                methods=['POST', 'GET'], website=True, csrf=False)
    def get_teacher_details(self, category_id=None, **kw):
        try:
            teacher = request.env['voca.teacher'].sudo().search([])
            categ = request.env['voca.teacher.categories'].sudo().search([])
            print("all teacher :", teacher, kw)
            if category_id:
                print("nnnnnnnnnn")
                teachers = request.env['voca.teacher'].sudo().search([('categories', '=', int(category_id))])
                return request.render('voca_studio_module.teacher_profile_card_with_category', {
                    'teachers': teachers,
                    'categories': categ,  # Optionally pass the category for UI
                })
            else:
                values = {
                    'teachers': teacher,
                    'categories': categ,
                }
                return request.render("voca_studio_module.teacher_profile_card", values)
        except Exception as e:
            return e

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
                 '/online-booking/package/<int:teacher_id>/<int:package_id>'], auth='public', website=True, csrf=True,methods=['GET'])
    def online_appointment(self, teacher_id=None,package_id=None, **kw):
        print("Package ------",package_id,teacher_id,kw)



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

        print("bookings_by_day",bookings_by_day)
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
        product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', int(teacher_id))],limit=1)
        teacher = request.env['voca.teacher'].sudo().search([('product_id', '=',product.id)])

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
        print("booooooooking by day", bookings_by_day)

        return json.dumps(bookings_by_day)




