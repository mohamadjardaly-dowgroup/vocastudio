from odoo.exceptions import UserError ,AccessDenied
from odoo.http import request
from odoo import http, tools, _
from odoo.addons.web.controllers.home import ensure_db, Home, SIGN_UP_REQUEST_PARAMS, LOGIN_SUCCESSFUL_PARAMS

import logging
_logger = logging.getLogger(__name__)

class VocaAuthLogin(Home):

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        response = super().web_login(*args, **kw)
        response.qcontext.update(self.get_auth_signup_config())
        print("information newwwwwww ", request.session.uid)
        uid = request.session.uid
        user = request.env['res.users'].sudo().browse(uid)
        print("user is ", user.partner_id)
        teacher = request.env['voca.teacher'].sudo().search([('instructor', '=', user.partner_id.id)])
        print("teacher is ", teacher.state, request.params['login_success'])
        if user and teacher.state in ['draft','refused']:
            print("helllooo")
            request.session.logout(keep_db=True)
            request.params['login_success'] = False
            return request.redirect('/teacher_restriction_page')
        else:
            return response
