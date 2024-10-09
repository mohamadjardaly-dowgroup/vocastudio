from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo import http
from odoo.http import request
import json


class BookingsCart(WebsiteSale):

    @http.route(['/shop/cart'], type='http', auth="public", website=True, sitemap=False)
    def cart(self, access_token=None, revive='', **post):
        print("rrrrrr")
        cart = super(BookingsCart, self).cart()
        return request.redirect('/shop/checkout?express=1')


class BookingController(http.Controller):

    @http.route('/save_booking_to_session', type='http', auth="public")
    def save_booking_to_session(self, **kwargs):
        # Get the selected bookings from the request

        selected_book = json.loads(kwargs.get('selected_book', {}))
        print("save_booking_to_session -------------", type(selected_book), selected_book)

        # Save the selected bookings in the session
        request.session['selected_bookings'] = selected_book

        return json.dumps([])

    @http.route('/get_booking_from_session', type='json', auth="public", methods=['GET'])
    def get_booking_from_session(self):
        # Retrieve bookings from the session
        bookings = request.session.get('selected_bookings', {})
        return {'bookings': bookings}
