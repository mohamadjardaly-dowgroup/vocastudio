from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MasterClass(models.Model):
    _name = 'master.classes'
    _description = 'MasterClass'

    name = fields.Char(string='Subject', default='New')

    image_1920 = fields.Image(string="Image")
    #samiha
    date = fields.Date(string=_('Starting Date'))

    time = fields.Char(string='Time')
    #samiha
    instructor = fields.Many2one('voca.teacher', string='Instructor',required=True)

    total_hours = fields.Float('Total Hours')

    lectures = fields.Integer(string="Lectures")

    categories = fields.Many2many('master.classes.categories', string='Category')
    description = fields.Text('Description')


    # New fields for booking date-time range
    datetime_from = fields.Datetime(string='Booking Start Time', required=True)
    datetime_to = fields.Datetime(string='Booking End Time',required=True)

    product_id = fields.Many2one('product.product', string='Product', readonly=True)


    dates_ids = fields.One2many('master.class.date', 'master_id', string='Dates')
    
    
    #samiha####################################################
    
    max_students = fields.Integer(string="Maximum Students", required=True)  # Add this field
    remaining_seats = fields.Integer(string="Remaining Seats", compute="_compute_remaining_seats", store=True)
    
    

    @api.depends('max_students')
    def _compute_remaining_seats(self):
        """Compute remaining seats based on bookings"""
        # for record in self:
        #     total_booked = sum(record.dates_ids.booking_master_ids.mapped('product_uom_qty'))
        #     record.remaining_seats = record.max_students - total_booked
        for master in self:
            master.remaining_seats = master.max_students
            # total_booked = sum(master.dates_ids.mapped('booking_order_id.product_uom_qty'))
            # master.remaining_seats = master.max_students - total_booked
    ##############################################################
            
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
        print('new maser class.................',master.name)
        product_vals = {
            'name': f"{master.name} - Master",
            'type': 'service',
            'is_master': True,
            'is_published':True,
            'master_class_id': master.id,  # Set the master_class_id field
        }
        print("product_vals....................", product_vals)
        product = self.env['product.product'].create(product_vals)
        master.product_id = product.id
        
        master_class_category = self.env.ref('voca_studio_module.master_class_category')
        master.categories = [(4, master_class_category.id)]
        
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

    name = fields.Char('Title', required=True, translate=True,compute='_compute_name')

    image_1920 = fields.Image(string="Image", readonly=False)  # image.mixin override

    @api.depends('name')
    def _compute_name(self):
        for record in self:
            record.name = 'cat'
    


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
        default='draft')
    
    #samiha####################################################
    max_students = fields.Integer(related='master_id.max_students', string="Maximum Students", readonly=True)
    remaining_seats = fields.Integer(string="Remaining Seats", compute="_compute_remaining_seats")

    @api.depends('booking_order_id.product_uom_qty')
    def _compute_remaining_seats(self):
        for record in self:
            total_booked = sum(record.booking_order_id.mapped('product_uom_qty'))
            record.remaining_seats = record.max_students - total_booked
    ############################################################
