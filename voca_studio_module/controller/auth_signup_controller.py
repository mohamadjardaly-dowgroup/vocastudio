from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError
from odoo.http import request
from odoo import http, tools, _
import psycopg2
import random
import string
from datetime import datetime


class VocaAuthSignupHome(AuthSignupHome):

    def get_auth_signup_qcontext(self):
        SIGN_UP_REQUEST_PARAMS_CUSTOM = ['first_name', 'nickname', 'phone', 'gender', 'birthday', 'role', 'experience','about']
        qcontext = super(VocaAuthSignupHome, self).get_auth_signup_qcontext()
        # qcontext['countries'] = request.env['res.country'].sudo().search([])
        # qcontext['countries'] = request.env['res.country'].sudo().search([])
        qcontext.update({k: v for (k, v) in request.params.items() if k in SIGN_UP_REQUEST_PARAMS_CUSTOM})
        print("qcontext ------------ >", qcontext)
        return qcontext

    def _prepare_signup_values(self, qcontext):
        # student_email = qcontext['login']
        # new_email = self.generate_address(student_email)
        # domain = 'selanuss.org'
        # qcontext['name'] = qcontext['first_name'] + ' ' + qcontext['nickname']
        # mail = self.create_ired_email(new_email, qcontext['name'], qcontext['password'],
        #                                        domain)
        # mail = self.create_ired_email(new_email, qcontext['name'], qcontext['password'],
        #                                            qcontext['domain'])
        # qcontext['login'] = mail
        values = {key: qcontext.get(key) for key in ('login', 'name', 'password', 'country_code',
                                                     'first_name', 'nickname', 'phone', 'gender', 'birthday', 'role',
                                                     'experience','about')}
        print("val ------------ >", values)
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        birthday_str = values.get('birthday')
        if birthday_str:
            try:
                # Convert the birthday string to a datetime object
                birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
            except ValueError:
                raise UserError(_("The birthday format is invalid. Please use YYYY-MM-DD."))
            # Calculate the age
            today = datetime.today().date()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            print("aaaaaaaage ", age)

            # Check if the age is under 18
            if age < 18:
                raise UserError(_("You must be at least 18 years old to register."))

        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang

        values["phone"] = f"{values.get('phone')}"
        values["name"] = f"{values.get('nickname')}"
        values["is_teacher"] = True
        # values["student_email"] = student_email
        # values["status"] = 'member'
        values['gender_1'] = values.get("gender")
        values['birthday'] = values.get("birthday")
        values['role'] = values.get("role")
        values['experience'] = values.get("experience")
        values['about'] = values.get("about")
        print("vaaaaaaaaalueees ", values['role'])



        return values

#     --------------------
