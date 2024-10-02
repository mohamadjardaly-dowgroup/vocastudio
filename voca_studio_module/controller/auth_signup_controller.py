from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError ,AccessDenied
from odoo.http import request
from odoo import http, tools, _
import werkzeug
from datetime import datetime
from odoo.addons.auth_signup.models.res_partner import SignupError
import logging
from odoo.tools.safe_eval import json
from werkzeug.urls import url_encode

_logger = logging.getLogger(__name__)


class VocaAuthSignupHome(AuthSignupHome):

    def get_auth_signup_qcontext(self):
        SIGN_UP_REQUEST_PARAMS_CUSTOM = ['first_name', 'nickname', 'phone', 'gender', 'birthday', 'role', 'experience',
                                         'about', 'is_teacher', 'attachment_ids']
        qcontext = super(VocaAuthSignupHome, self).get_auth_signup_qcontext()
        # qcontext['countries'] = request.env['res.country'].sudo().search([])
        # qcontext['countries'] = request.env['res.country'].sudo().search([])
        qcontext.update({k: v for (k, v) in request.params.items() if k in SIGN_UP_REQUEST_PARAMS_CUSTOM})
        print("qcontext ------------ >", qcontext)
        return qcontext

    def _prepare_signup_values(self, qcontext):
        values = {key: qcontext.get(key) for key in ('login', 'name', 'password', 'country_code',
                                                     'first_name', 'nickname', 'phone', 'gender', 'birthday', 'role',
                                                     'experience', 'about', 'is_teacher', 'attachment_ids')}
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
        # values["is_teacher"] = True
        # values["student_email"] = student_email
        # values["status"] = 'member'
        values['gender_1'] = values.get("gender")
        values['birthday'] = values.get("birthday")
        values['role'] = values.get("role")
        values['experience'] = values.get("experience")
        values['about'] = values.get("about")

        return values

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        print("vaaaaaaaaalueees ", request.httprequest.files)
        qcontext = self.get_auth_signup_qcontext()
        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Send an account creation confirmation email
                User = request.env['res.users']
                user_sudo = User.sudo().search(
                    User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                )
                template = request.env.ref('auth_signup.mail_template_user_signup_account_created',
                                           raise_if_not_found=False)
                if user_sudo and template:
                    template.sudo().send_mail(user_sudo.id, force_send=True)

                upload_cv_dict_str = kw.get('file_base64_dict', '{}')
                upload_cv_dict = json.loads(upload_cv_dict_str)
                if upload_cv_dict:
                    attachments_ids = []
                    for key, value in zip(upload_cv_dict.keys(), upload_cv_dict.values()):
                        attachment_id = request.env['ir.attachment'].sudo().create({
                            'name': key,
                            'res_model': 'res.partner',
                            'res_id': user_sudo.partner_id.id,
                            'type': 'binary',
                            'datas': value,
                        })
                        attachments_ids.append(attachment_id.id)
                    user_sudo.partner_id.write({'attachment_ids': [(6, 0, attachments_ids)]})
                print("ressssssssssssss ", qcontext)
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.warning("%s", e)
                    qcontext['error'] = _("Could not create a new account.") + "\n" + str(e)

        elif 'signup_email' in qcontext:
            print("i am heeer ", qcontext)
            user = request.env['res.users'].sudo().search(
                [('email', '=', qcontext.get('signup_email')), ('state', '!=', 'new')], limit=1)
            if user:
                return request.redirect('/web/login?%s' % url_encode({'login': user.login, 'redirect': '/web'}))

        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response
