import re
import requests
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
        if not phone or not phone[:].isdigit():
            raise UserError(_("Phone number must contain only digits (e.g., 123456789)."))

    def _validate_cv(self, upload_cv_dict, role):
        """Ensure CV is uploaded if the user is a teacher."""
        if role == 'teacher' and not upload_cv_dict:
            raise UserError(_("A CV is required for teachers. Please upload your CV."))

    def get_auth_signup_qcontext(self):
        """Extend context with additional fields for signup."""
        SIGN_UP_REQUEST_PARAMS_CUSTOM = [
            'first_name', 'nickname', 'phone', 'gender', 'birthday', 'role',
            'experience', 'about', 'is_teacher', 'attachment_ids','instrument','level','terms'
        ]
        qcontext = super(VocaAuthSignupHome, self).get_auth_signup_qcontext()
        qcontext.update({k: v for (k, v) in request.params.items() if k in SIGN_UP_REQUEST_PARAMS_CUSTOM})
        
        # Debug: Check request headers
        user_ip = request.httprequest.headers.get('X-Forwarded-For', request.httprequest.remote_addr)

        if user_ip:
            # If multiple IPs exist in X-Forwarded-For, take the first one
            if ',' in user_ip:
                user_ip = user_ip.split(',')[0]

        _logger.info(f"Detected User IP: {user_ip}")  # Log IP for debugging

        try:
            # Step 1: Check if we have a valid IP
            if user_ip and user_ip not in ['127.0.0.1', 'localhost']:
                # Step 2: Query GeoIP API
                response = requests.get(f"https://ipapi.co/{user_ip}/json/")
                if response.status_code == 200:
                    data = response.json()
                    user_country_code = data.get('country_code')
                    
                    print("data is ",data)
                    print("user_country_code is ",user_country_code)
                    

                    if user_country_code:
                        user_country = request.env['res.country'].sudo().search([('code', '=', user_country_code)], limit=1)
                        if user_country:
                            qcontext['default_country_id'] = user_country.id
                            _logger.info(f"Default Country ID Set: {user_country.id} - {user_country.name}")

        except Exception as e:
            _logger.warning("GeoIP API Error: %s", str(e))
        
        return qcontext

    

    def _prepare_signup_values(self, qcontext):
        """Prepare and validate signup values."""
        values = {key: qcontext.get(key) for key in (
            'login', 'name', 'password', 'first_name', 'nickname', 'phone', 'gender', 
            'birthday', 'role', 'experience', 'about', 'is_teacher','instrument'
        )}
        
        if not qcontext.get("terms"):
            raise UserError("You must accept the Terms and Conditions to proceed.")
            
        restricted_words = ["free", "promo", "bitcoin", "money", "offer"]
        special_chars_pattern = re.compile(r"[^a-zA-Z\s]")  # No special characters
        nickname = values.get("nickname", "").strip().lower()

        if any(word in nickname for word in restricted_words):
            raise UserError("Invalid username: It contains restricted words.")

        if special_chars_pattern.search(nickname):
            raise UserError("Invalid username: Special characters are not allowed.")

        if len(nickname) < 3:
            raise UserError("Invalid username: Must be at least 3 characters long.")
        if values.get('role') == 'student':
            print("inside the if role is student .............. ")
            level = qcontext.get('level')
            print("level is .............. ",level)
            if level:
                level_tag = request.env['res.partner.category'].sudo().search([('name', '=', level)], limit=1)
                print("level_tag is........... ",level_tag)
                if not level_tag:
                    level_tag = request.env['res.partner.category'].sudo().create({'name': level})
                    print("level_tag is  if not......... ",level_tag)
                values['category_id'] = [(4, level_tag.id)]  # Assign the level as a tag
                print("values['category_id'] is ........ ",values['category_id'])
        if values.get('role') == 'teacher' and not values.get('instrument'):
            raise UserError(_("Instrument field is required for teachers. Please specify the instrument you teach."))
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
        values['instrument'] = values.get('instrument')
        if values.get('role') == 'student':
            values.update({'role': 'stu'})

        country_id = qcontext.get('country_id')
        if country_id:
            country = request.env['res.country'].sudo().browse(int(country_id))
            values['country_id'] = int(country_id)  # Store country in res.partner

        # Append phone code to the phone number
        if country and country.phone_code:
            values['phone'] = f"+{country.phone_code} {values.get('phone', '')}".strip()

        return values

    @http.route('/web/signup/<string:role>', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, role, *args, **kw):
        #Verify CAPTCHA
        recaptcha_response = kw.get('g-recaptcha-response')
        secret_key = '6LcM3xMrAAAAAFaw38z7jqD4rZN9A71Fu6RAbzEW'

        captcha_check = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': secret_key,
                'response': recaptcha_response
            }
        ).json()

        if not captcha_check.get('success'):
            # Re-render signup page with error
            return request.render('auth_signup.signup', {
                'error': 'CAPTCHA validation failed. Please try again.',
                'values': kw,
            })
        """Handle web signup with role-based validations."""
        qcontext = self.get_auth_signup_qcontext()
        qcontext['role'] = role
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
