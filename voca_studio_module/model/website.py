# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, _lt, SUPERUSER_ID, api, fields, models, tools
from odoo.http import request
from datetime import datetime,timedelta


class Website(models.Model):
    _inherit = 'website'

    def sale_get_order(self, force_create=False, update_pricelist=False):
        sale_order = super().sale_get_order(force_create, update_pricelist)
        first_order_line = sale_order.order_line[:1]  # This fetches only the first order line

        if request and request.session and request.session.get('package_id'):
            sale_order.write({'package_id': request.session.get('package_id').get('id')})
            selected_bookings = request.session.get('selected_bookings')
            if selected_bookings:
                booking_dates = list(selected_bookings.get('selected_book').keys())
                date_format = '%a %b %d %Y %H:%M:%S GMT%z'
                booking_lines = self.env['voca.teacher.booking.lines'].search([
                    ('availablity_date', 'in', [
                        (datetime.strptime(date.split(' (')[0], date_format) - timedelta(hours=3)).replace(tzinfo=None)
                        for date in booking_dates
                    ])
                ])
                print("bobobobo", booking_lines,first_order_line)
                if first_order_line:
                    first_order_line.write({
                        'price_unit':request.session.get('package_id').get('price'),
                        'booking_ids': [(6, 0, booking_lines.ids)]})


        return sale_order
