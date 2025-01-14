from odoo import _, _lt, SUPERUSER_ID, api, fields, models, tools
from odoo.http import request
from datetime import datetime,timedelta
import logging

_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = 'website'

    def sale_get_order(self, force_create=False, update_pricelist=False):
        sale_order = super().sale_get_order(force_create, update_pricelist)
        print("Sale Order product id:..................", sale_order.id)
        print("Sale Order:..................", sale_order)
        first_order_line = sale_order.order_line[:1]  # This fetches only the first order line
        print("First Order Line:.........................", first_order_line)

        selected_bookings = request.session.get('selected_bookings')
        teacher_id = request.session.get('teacher_id').get('teacher_id')
        print("Teacher ID:..................", teacher_id)
        print("Selected Bookings:", selected_bookings)
        if selected_bookings:
                booking_dates = selected_bookings.get('selected_book', [])
                # Adjust the date format to match the incoming data
                date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
                # date_format = '%a %b %d %Y %H:%M:%S GMT%z'
                parsed_dates = self.env['voca.teacher.booking.lines'].search([
                   ('availablity_date', 'in', [
                       (datetime.strptime(date.split(' (')[0], date_format) + timedelta(hours=2)).replace(tzinfo=None)
                       for date in booking_dates
                   ])
               ])
              #  booking_master_lines = self.env['master.class.date'].search([
              #      ('date', 'in', [
                #        (datetime.strptime(date.split(' (')[0], date_format) - timedelta(hours=3)).replace(tzinfo=None)
                #        for date in booking_dates
                #    ])
                #])
                # Convert the booking dates to a format compatible with your search
                # parsed_dates = [
                #     (datetime.strptime(date, date_format) - timedelta(hours=3)).replace(tzinfo=None)
                #     for date in booking_dates
                # ]
                print("Parsed Dates:...", parsed_dates)
                booking_lines = self.env['voca.teacher.booking.lines'].search([('availablity_date', 'in', parsed_dates)])
                print("Booking Lines:.....", booking_lines)
                booking_master_lines = self.env['master.class.date'].search([('date', 'in', parsed_dates)])

                # Update the first order line with booking information
                if first_order_line:
                    print('i am inside first order line.....', first_order_line)
                    if booking_lines:
                        first_order_line.write({
                            # 'price_unit': request.session.get('package_id').get('price'),
                            'booking_ids': [(6, 0, booking_lines.ids)],
                        })
                    else:
                        booking_master_lines.write({'status': 'booked'})
                        first_order_line.write({
                            # 'price_unit': request.session.get('package_id').get('price'),
                            'booking_master_ids': [(6, 0, booking_master_lines.ids)],
                        })
        return sale_order
