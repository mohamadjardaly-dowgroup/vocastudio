from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    package_id = fields.Many2one('voca.teacher.packaging.lines', string='Teacher package')
    seats_reserved = fields.Boolean(string="Masterclass seats reserved", default=False)

    def write(self, vals):
        # Run only when the state actually becomes 'sent'
        run_on_sent = vals.get('state') == 'sent'
        res = super().write(vals)
        if run_on_sent:
            for order in self:
                if order.state == 'sent' and not order.seats_reserved:
                    order._process_booking_lines()
        return res

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if not order.seats_reserved:
                order._process_booking_lines()
        return res

    def _process_booking_lines(self):
        for order in self:
            if order.seats_reserved:
                continue

            # Only consider lines that are actually relevant:
            # - masterclass product, or
            # - has concrete booking records (single or master)
            relevant_lines = order.order_line.filtered(
                lambda l: bool(l.product_id.is_master or l.booking_ids or l.booking_master_ids)
            )
            if not relevant_lines:
                # Nothing to do for this order; mark as processed to avoid re-entry
                order.seats_reserved = True
                continue

            for line in relevant_lines:
                # 1) Update bookings, if any
                # if line.booking_ids:
                #     line.booking_ids.write({'status': 'booked', 'lesson_state': 'upcoming'})
                if line.booking_ids:
                    booking_vals = {
                        'status': 'booked',
                        'lesson_state': 'upcoming',
                    }

                    if line.lesson_program_id:
                        booking_vals.update({
                            'booking_type': 'lesson_program',
                            'lesson_program_id': line.lesson_program_id.id,
                        })

                    line.booking_ids.write(booking_vals)
                    
    
                if line.booking_master_ids:
                    line.booking_master_ids.write({'status': 'booked'})

                # 2) Masterclass seat handling (only for masterclass products)
                if line.product_id.is_master:
                    master_class = line.product_id.master_class_id
                    if master_class:
                        total_seats_needed = line.product_uom_qty
                        if master_class.remaining_seats < total_seats_needed:
                            raise ValidationError(_("Not enough seats available for the master class."))
                        master_class.write({
                            'remaining_seats': master_class.remaining_seats - total_seats_needed
                        })

                    # Guest email if the buyer is not a portal user
                    # if not order.partner_id.user_ids:
                    self._send_guest_masterclass_email(order.partner_id, line)

                # 3) Teacher email only if it’s actually a class/booking line
                #    (masterclass OR has bookings). Never for regular products.
                if (line.product_id.is_master or line.booking_ids or line.booking_master_ids) and not line.teacher_emailed:
                    teacher_packaging_line = self.env['voca.teacher.packaging.lines'].search(
                        [('product_id', '=', line.product_id.id)], limit=1
                    )
                    if teacher_packaging_line:
                        teacher = teacher_packaging_line.package_id
                        if teacher and teacher.instructor and teacher.instructor.email:
                            self._send_teacher_email(teacher.instructor, line)
                            line.teacher_emailed = True

            # Mark after all relevant lines are processed to make it idempotent
            order.seats_reserved = True

    def _send_teacher_email(self, teacher, sale_order_line):
        email_template = self.env.ref('voca_studio_module.mail_template_lesson_booking_teacher')
        if email_template:
            email_template.sudo().send_mail(sale_order_line.id, force_send=True)

    def _send_guest_masterclass_email(self, partner, sale_order_line):
        if not partner.email:
            return
        template_id = self.env.ref('voca_studio_module.email_template_guest_masterclass')
        if template_id:
            template_id.sudo().send_mail(sale_order_line.id, force_send=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    
    lesson_program_id = fields.Many2one(
        "voca.lesson.program",
        string="Lesson Program",
    )

    booking_ids = fields.One2many('voca.teacher.booking.lines', 'booking_order_id', string='Booking')
    booking_master_ids = fields.One2many('master.class.date', 'booking_order_id', string='Booking master')
    package_id = fields.Many2one('voca.teacher.packaging.lines', string='Package')

    lesson_state = fields.Selection([
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled')
    ], string='Status', default='upcoming')

    converted_price = fields.Float(string="Converted Price", store=True)

    # Idempotency flag so teacher doesn’t get emailed twice for this line
    teacher_emailed = fields.Boolean(string="Teacher emailed", default=False)
    
    def _get_displayed_quantity(self):
        """
        Fallback needed because the website cart template calls this method.
        Some Odoo setups/views expect it from website sale stock logic.
        """
        self.ensure_one()
        return self.product_uom_qty

    def _get_max_available_qty(self):
        """
        Fallback needed because the website cart template calls this method.
        For service products, including lesson programs, stock should not limit quantity.
        """
        self.ensure_one()

        if not self.product_id or self.product_id.type != 'product':
            return 0

        try:
            return self.product_id.free_qty
        except Exception:
            return 0
    
    @api.depends('product_id', 'product_uom', 'product_uom_qty', 'package_id', 'lesson_program_id', 'converted_price')
    def _compute_price_unit(self):
        for line in self:

            # Lesson Program:
            # Example: total price = 600, sessions = 5
            # sale qty = 5, unit price must be 120
            if line.lesson_program_id:
                session_count = line.lesson_program_id.session_count or line.product_uom_qty or 1.0
                line.product_uom_qty = session_count

                if line.converted_price:
                    line.price_unit = line.converted_price / session_count
                else:
                    line.price_unit = line.lesson_program_id.price / session_count

                continue

            # Existing teacher package logic
            if line.package_id:
                if line.converted_price:
                    line.product_uom_qty = line.package_id.quantity
                    line.price_unit = line.converted_price / line.product_uom_qty
                else:
                    line.product_uom_qty = line.package_id.quantity
                    line.price_unit = line.package_id.price / line.product_uom_qty

                continue

            # Default Odoo sale price logic
            if line.qty_invoiced > 0 or (line.product_id.expense_policy == 'cost' and line.is_expense):
                continue

            if not line.product_uom or not line.product_id:
                line.price_unit = 0.0
            else:
                line = line.with_company(line.company_id)
                price = line._get_display_price()
                line.price_unit = line.product_id._get_tax_included_unit_price_from_price(
                    price,
                    line.currency_id or line.order_id.currency_id,
                    product_taxes=line.product_id.taxes_id.filtered(lambda t: t.company_id == line.env.company),
                    fiscal_position=line.order_id.fiscal_position_id,
                )

    # @api.depends('product_id', 'product_uom', 'product_uom_qty', 'package_id')
    # def _compute_price_unit(self):
    #     for line in self:
    #         if line.package_id:
    #             if line.converted_price:
    #                 line.product_uom_qty = line.package_id.quantity
    #                 line.price_unit = line.converted_price / line.product_uom_qty
    #             else:
    #                 line.product_uom_qty = line.package_id.quantity
    #                 line.price_unit = line.package_id.price / line.product_uom_qty
    #         else:
    #             if line.qty_invoiced > 0 or (line.product_id.expense_policy == 'cost' and line.is_expense):
    #                 continue
    #             if not line.product_uom or not line.product_id:
    #                 line.price_unit = 0.0
    #             else:
    #                 line = line.with_company(line.company_id)
    #                 price = line._get_display_price()
    #                 line.price_unit = line.product_id._get_tax_included_unit_price_from_price(
    #                     price,
    #                     line.currency_id or line.order_id.currency_id,
    #                     product_taxes=line.product_id.taxes_id.filtered(lambda t: t.company_id == line.env.company),
    #                     fiscal_position=line.order_id.fiscal_position_id,
    #                 )
