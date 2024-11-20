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
                
                teacher_data = []
                category_data=[]
                for t in teacher:
                    teacher_data.append({
                        'id': t.id,
                        'name': t.name,
                        'experience': t.experience,
                        'categories':  [{'id': cat.id, 'name': cat.name} for cat in t.categories],
                        'language': t.language,
                        'about': t.about or '',
                        'image_url': f"/web/image/voca.teacher/{t.id}/image_1920",
                    })
                for category in categ:
                    category_data.append({
                        'id': category.id,
                        'name': category.name,
                        'image_url': f"/web/image/voca.teacher.categories/{category.id}/image_1920",
                    })
                values = {
                    'teachers': teacher_data,
                    'categories': category_data,
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
            # teacher = request.env['master.classes'].sudo().search([])
            categ = request.env['master.classes.categories'].sudo().search([])
            # print("all teacher :", teacher, kw)
            master = request.env['master.classes'].sudo().search([('categories', '=', int(category_id))])
            print("master", master)

            return request.render('voca_studio_module.master_class_card_with_category', {
                'master': master,  # Optionally pass the category for UI
            })
        except Exception as e:
            return e

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
