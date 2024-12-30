from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MasterClass(models.Model):
    _name = 'master.classes'
    _description = 'MasterClass'

    name = fields.Char(string='Subject', default='New')

    image_1920 = fields.Image(string="Image")

    date = fields.Date(string=_('Date'))

    time = fields.Char(string='Time')

    instructor = fields.Many2one('voca.teacher', string='Instructor')

    total_hours = fields.Float('Total Hours')

    lectures = fields.Integer(string="Lectures")

    categories = fields.Many2many('master.classes.categories', string='Category',required=True)
    description = fields.Text('Description')


    # New fields for booking date-time range
    datetime_from = fields.Date(string='Booking Start Time')
    datetime_to = fields.Date(string='Booking End Time')

    product_id = fields.Many2one('product.product', string='Product', readonly=True)


    dates_ids = fields.One2many('master.class.date', 'master_id', string='Dates')

    @api.onchange('datetime_from', 'datetime_to')
    def _onchange_datetime_range(self):
        if self.datetime_from and self.datetime_to and self.datetime_from < self.datetime_to:
            # Clear existing dates
            self.dates_ids = [(5, 0, 0)]

            # Generate dates between datetime_from and datetime_to
            start_date = fields.Date.from_string(self.datetime_from)
            end_date = fields.Date.from_string(self.datetime_to)
            date_list = []

            current_date = start_date
            while current_date <= end_date:
                date_list.append((0, 0, {'date': current_date}))
                current_date += timedelta(days=1)

            # Assign dates to dates_ids field
            self.dates_ids = date_list


    @api.model
    def create(self, vals):
        master = super(MasterClass, self).create(vals)
        # Automatically create a product linked to this package
        print("vaaaals ", vals, master.name)
        product_vals = {
            'name': f"{master.name} - Master",
            'type': 'service',
            'is_master': True,
            # 'list_price': package.price,
        }
        product = self.env['product.product'].create(product_vals)
        master.product_id = product.id
        return master




    @api.constrains('datetime_from', 'datetime_to')
    def _check_datetime_range(self):
        for record in self:
            if record.datetime_from and record.datetime_to:
                if record.datetime_from >= record.datetime_to:
                    raise ValidationError(_("The booking start time must be before the end time."))


class MasterClassCategories(models.Model):
    _name = 'master.classes.categories'
    # _description = 'Portal'

    name = fields.Char('Title', required=True, translate=True)

    image_1920 = fields.Image(string="Image", readonly=False)  # image.mixin override



class MasterClassDate(models.Model):
    _name = 'master.class.date'
    _description = 'Master Class Date'

    master_id = fields.Many2one('master.classes', string='Master Class', required=True, ondelete='cascade')
    date = fields.Date(string='Date', required=True)
    booking_order_id = fields.Many2one('sale.order.line', string='Booking')

    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('booked', 'Booked'),
        ], string='Status', index=True, readonly=True, copy=False,
        default='draft', tracking=True)
