import re
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError, AccessDenied
from odoo.http import request
from odoo import http, _
from datetime import datetime
from odoo.addons.auth_signup.models.res_partner import SignupError
import logging
import json
from werkzeug.urls import url_encode
import werkzeug

_logger = logging.getLogger(__name__)


class VocaAuthSignupHome(AuthSignupHome):
    def _validate_email(self, email):
        """Validate email format."""
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not email or not re.match(email_regex, email):
            raise UserError(_("Please provide a valid email address."))

    def _validate_phone(self, phone):
        """Validate phone format to include a country code."""
        if not phone or not phone.startswith('+') or not phone[1:].isdigit():
            raise UserError(_("Phone number must include a valid country code (e.g., +123456789)."))

    def _validate_cv(self, upload_cv_dict, role):
        """Ensure CV is uploaded if the user is a teacher."""
        if role == 'teacher' and not upload_cv_dict:
            raise UserError(_("A CV is required for teachers. Please upload your CV."))

    def get_auth_signup_qcontext(self):
        """Extend context with additional fields for signup."""
        SIGN_UP_REQUEST_PARAMS_CUSTOM = [
            'first_name', 'nickname', 'phone', 'gender', 'birthday', 'role',
            'experience', 'about', 'is_teacher', 'attachment_ids'
        ]
        qcontext = super(VocaAuthSignupHome, self).get_auth_signup_qcontext()
        qcontext.update({k: v for (k, v) in request.params.items() if k in SIGN_UP_REQUEST_PARAMS_CUSTOM})
        return qcontext

    def _prepare_signup_values(self, qcontext):
        """Prepare and validate signup values."""
        values = {key: qcontext.get(key) for key in (
            'login', 'name', 'password', 'first_name', 'nickname', 'phone', 'gender', 
            'birthday', 'role', 'experience', 'about', 'is_teacher'
        )}
        # Validate email
        if not values.get('login'):
            raise UserError(_("The email field is required."))
        self._validate_email(values.get('login'))

        # Validate phone
        self._validate_phone(values.get('phone'))

        # Validate passwords
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))

        # Validate birthday and calculate age
        birthday_str = values.get('birthday')
        if birthday_str:
            try:
                birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
                today = datetime.today().date()
                age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
                # Role-based age validation
                if values.get('role') == 'teacher' and age < 18:
                    raise UserError(_("You must be at least 18 years old to register as a teacher."))
                elif values.get('role') == 'student' and age > 18:
                    _logger.warning("Student age is above 18, but this is allowed.")
            except ValueError:
                raise UserError(_("The birthday format is invalid. Please use YYYY-MM-DD."))

        # Additional fields
        values['name'] = values.get('nickname')
        if values.get('role') == 'student':
            values.update({'role': 'stu'})

        return values

    @http.route('/web/signup/<string:role>', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, role, *args, **kw):
        """Handle web signup with role-based validations."""
        qcontext = self.get_auth_signup_qcontext()
        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                # Decode CV upload
                upload_cv_dict_str = kw.get('file_base64_dict', '{}')
                upload_cv_dict = json.loads(upload_cv_dict_str) if upload_cv_dict_str else {}

                # Validate CV for teachers
                self._validate_cv(upload_cv_dict, role)

                # Prepare signup values
                self.do_signup(qcontext)

                # Find created user and send confirmation email
                User = request.env['res.users']
                user_sudo = User.sudo().search(
                    User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                )
                template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
                if user_sudo and template:
                    template.sudo().send_mail(user_sudo.id, force_send=True)

                # Attach CVs to the user's partner record
                if upload_cv_dict:
                    attachments_ids = []
                    for key, value in upload_cv_dict.items():
                        attachment_id = request.env['ir.attachment'].sudo().create({
                            'name': key,
                            'res_model': 'res.partner',
                            'res_id': user_sudo.partner_id.id,
                            'type': 'binary',
                            'datas': value,
                        })
                        attachments_ids.append(attachment_id.id)
                    user_sudo.partner_id.write({'attachment_ids': [(6, 0, attachments_ids)]})

                return self.web_login(*args, **kw)

            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env['res.users'].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext['error'] = _("Another user is already registered using this email address.")
                else:
                    _logger.warning("%s", e)
                    qcontext['error'] = _("Could not create a new account.") + "\n" + str(e)

        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response
