# -*- coding: utf-8 -*-

from odoo import http, modules, tools
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class TeacherController(http.Controller):

    # @http.route(['/'], type='http', auth="public",
    #             methods=['POST', 'GET'], website=True, csrf=False)
    # def get_teacher_details(self, **kw):
    #     try:
    #         teacher = request.env['voca.teacher'].sudo().search([])
    #         user = request.env.user.has_group("base.group_portal")
    #
    #         print("all teacher :", teacher, user)
    #         values = {
    #             'teacher_id': teacher,
    #         }
    #         return request.render("voca_studio_module.homepage", values)
    #
    #
    #     except Exception as e:
    #         return e


    @http.route(['/teacher_profile',
                 '/teacher_profile/cat/<int:category_id>'], type='http', auth="public",
                methods=['POST', 'GET'], website=True, csrf=False)
    def get_teacher_details(self,category_id=None, **kw):
        try:
            teacher = request.env['voca.teacher'].sudo().search([])
            categ = request.env['voca.teacher.categories'].sudo().search([])
            print("all teacher :", teacher)
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
    def get_full_profile(self, teacher_id=None,category_id=None, **kw):
        print("tttttttttttttttt",teacher_id,category_id,**kw)

        teacher = request.env['voca.teacher'].sudo().browse(teacher_id)
        if not teacher.exists():
            return request.not_found()

        return request.render('voca_studio_module.teacher_profile_template', {
            'teacher': teacher,
        })

    @http.route(['/online-booking'], auth='public', website=True, csrf=True)
    def online_appointment(self, **kw):
        if request.env.user._is_public():

            return request.redirect('web/login')
        # values = self.prepare_values(default_appointee_id=kw.get('appointee', False))

        return request.render('voca_studio_module.available_days_list_with_times')

    @http.route('/teacher_restriction_page', type='http', auth='public', website=True)
    def teacher_restriction_page(self, **kwargs):
        return request.render('voca_studio_module.teacher_login_restriction', {})



