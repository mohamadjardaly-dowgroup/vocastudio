from odoo.exceptions import UserError
from odoo.http import request
from odoo import http, tools, _

import base64
import psycopg2
import random
import string
from datetime import datetime
from odoo.http import route, Controller, request

from odoo.addons.portal.controllers.portal import CustomerPortal


class VocaEditController(CustomerPortal):

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post and request.httprequest.method == 'POST':
            self.MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id"]
            self.OPTIONAL_BILLING_FIELDS += ["zipcode", "state_id", "vat", "company_name", "category_ids", "tag_ids"]
            if not partner.can_edit_vat():
                post['country_id'] = str(partner.country_id.id)

            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:

                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})

                if 'category_ids' in post:
                    # Convert category_ids from string to list of integers
                    category_ids = list(map(int, post['category_ids'].split(','))) if post['category_ids'] else []
                    values['category_ids'] = category_ids

                if 'tag_ids' in post:
                    # Convert tag_ids from string to list of integers
                    tag_ids = list(map(int, post['tag_ids'].split(','))) if post['tag_ids'] else []
                    values['tag_ids'] = tag_ids

                # if 'image_1920' in post:
                #     image_file =  post.get('image_1920')
                #     if image_file:
                #         image_1920 = base64.b64encode(image_file.read())  # Read the file content
                #         image_1920 = base64.b64encode(image_1920)  # Encode the image content to base64
                #         values['image_1920'] = image_1920

                print("Values being written to partner:", set(values.keys()))

                for field in set(['country_id', 'state_id']) & set(values.keys()):
                    try:
                        print("iteration ",values[field])
                        values[field] = [int(values[field])]
                    except:
                        values[field] = False

                values.update({'zip': values.pop('zipcode', '')})
                self.on_account_update(values, partner)
                print("Values being written to partner:", values)
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        categories = request.env['voca.teacher.categories'].sudo().search([])
        tags = request.env['voca.teacher.tags'].sudo().search([])

        values.update({
            'partner': partner,
            'countries': countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'partner_can_edit_vat': partner.can_edit_vat(),
            'redirect': redirect,
            'page_name': 'my_details',
            'categories': categories,
            'tags': tags,
        })
        print("values in my account ", values)

        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response
