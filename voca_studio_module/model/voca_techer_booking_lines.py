from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import pytz


class TeacherBooking(models.Model):
    _name = "voca.teacher.booking.lines"
    _rec_name = "availablity_date"

    name = fields.Char(
        string="Name",
        translate=True,
    )

    booking_type = fields.Selection(
        selection=[
            ("private_lesson", "Private Lesson"),
            ("lesson_program", "Lesson Program"),
        ],
        string="Booking Type",
        default="private_lesson",
        required=True,
    )

    lesson_program_id = fields.Many2one(
        comodel_name="voca.lesson.program",
        string="Lesson Program",
    )

    lesson_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("upcoming", "Upcoming"),
            ("completed", "Completed"),
            ("canceled", "Canceled"),
        ],
        string="Lesson State",
        default="draft",
        required=True,
    )

    booking_id = fields.Many2one(
        comodel_name="voca.teacher",
        string="Teacher",
    )

    booking_order_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Booking",
    )

    availablity_date = fields.Datetime(
        string="Date",
        required=True,
    )

    status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("booked", "Booked"),
            ("refused", "Refused"),
        ],
        string="Status",
        index=True,
        readonly=True,
        copy=False,
        default="approved",
        tracking=True,
    )

    lesson_date_local = fields.Char(
        string="Lesson Date (Local)",
        compute="_compute_lesson_dates",
        store=False,
    )

    # -------------------------------------------------------------------------
    # Timezone display
    # -------------------------------------------------------------------------

    @api.depends(
        "availablity_date",
        "booking_order_id",
        "booking_order_id.order_id.partner_id",
        "booking_order_id.order_id.partner_id.tz",
    )
    def _compute_lesson_dates(self):
        """Display the lesson datetime using the student's timezone."""

        for record in self:
            record.lesson_date_local = ""

            if not record.availablity_date:
                continue

            student = record.booking_order_id.order_id.partner_id
            student_timezone = student.tz or "UTC"

            try:
                timezone = pytz.timezone(student_timezone)

                utc_datetime = record.availablity_date

                # Odoo Datetime values are normally naive UTC values.
                if utc_datetime.tzinfo is None:
                    utc_datetime = pytz.UTC.localize(utc_datetime)
                else:
                    utc_datetime = utc_datetime.astimezone(pytz.UTC)

                local_datetime = utc_datetime.astimezone(timezone)

                record.lesson_date_local = local_datetime.strftime(
                    "%d %B %Y, %I:%M %p"
                )

            except (pytz.UnknownTimeZoneError, ValueError, TypeError):
                record.lesson_date_local = fields.Datetime.to_string(
                    record.availablity_date
                )

    # -------------------------------------------------------------------------
    # Lesson Program automatic synchronization
    # -------------------------------------------------------------------------

    def _find_lesson_program_from_sale_line(self, sale_line):
        """
        Find the Lesson Program related to the sale order line.

        It first checks sale_line.lesson_program_id. If that field is empty,
        it detects the program from the generated product.
        """
        self.ensure_one()

        if not sale_line:
            return self.env["voca.lesson.program"]

        if sale_line.lesson_program_id:
            return sale_line.lesson_program_id

        if not sale_line.product_id:
            return self.env["voca.lesson.program"]

        return self.env["voca.lesson.program"].sudo().search(
            [
                ("product_id", "=", sale_line.product_id.id),
            ],
            limit=1,
        )

    @api.onchange("booking_order_id", "lesson_state")
    def _onchange_booking_order_lesson_program(self):
        """
        Fill the technical Lesson Program fields immediately in the form.

        The administrator only needs to:
        1. Select the sale order line.
        2. Set Lesson State to Upcoming.
        """
        for booking in self:
            sale_line = booking.booking_order_id

            if not sale_line:
                continue

            program = booking._find_lesson_program_from_sale_line(sale_line)

            if not program:
                continue

            booking.booking_type = "lesson_program"
            booking.lesson_program_id = program
            booking.booking_id = program.teacher_id

            if booking.lesson_state == "upcoming":
                booking.status = "booked"

    def _sync_lesson_program_from_sale_line(self):
        """
        Synchronize the booking after saving.

        This supports the required backend workflow:
        - create and confirm a sales order using the program product;
        - open the teacher booking line;
        - select the sale order line;
        - change Lesson State to Upcoming.
        """
        if self.env.context.get("skip_lesson_program_auto_sync"):
            return

        for booking in self:
            sale_line = booking.booking_order_id

            # The booking was disconnected from its previous sale order line.
            if not sale_line:
                if booking.booking_type == "lesson_program":
                    reset_values = {
                        "booking_type": "private_lesson",
                        "lesson_program_id": False,
                    }

                    if booking.status == "booked":
                        reset_values["status"] = "approved"

                    if booking.lesson_state == "upcoming":
                        reset_values["lesson_state"] = "draft"

                    booking.with_context(
                        skip_lesson_program_auto_sync=True
                    ).sudo().write(reset_values)

                continue

            program = booking._find_lesson_program_from_sale_line(sale_line)

            # Normal teacher package/private lesson:
            # leave its existing behavior unchanged.
            if not program:
                continue

            # Store the detected program on the sale order line.
            # The Student and Teacher Lesson Series dashboards use this field.
            if not sale_line.lesson_program_id:
                sale_line.sudo().write({
                    "lesson_program_id": program.id,
                })

            booking_values = {}

            if booking.booking_type != "lesson_program":
                booking_values["booking_type"] = "lesson_program"

            if booking.lesson_program_id != program:
                booking_values["lesson_program_id"] = program.id

            if booking.booking_id != program.teacher_id:
                booking_values["booking_id"] = program.teacher_id.id

            if (
                booking.lesson_state == "upcoming"
                and booking.status != "booked"
            ):
                booking_values["status"] = "booked"

            if booking_values:
                booking.with_context(
                    skip_lesson_program_auto_sync=True
                ).sudo().write(booking_values)

    @api.model_create_multi
    def create(self, vals_list):
        bookings = super().create(vals_list)
        bookings._sync_lesson_program_from_sale_line()
        return bookings

    def write(self, vals):
        result = super().write(vals)

        fields_triggering_sync = {
            "booking_order_id",
            "lesson_state",
            "booking_type",
            "lesson_program_id",
        }

        should_sync = bool(
            fields_triggering_sync.intersection(vals.keys())
        )

        if (
            should_sync
            and not self.env.context.get("skip_lesson_program_auto_sync")
        ):
            self._sync_lesson_program_from_sale_line()

        return result

    # -------------------------------------------------------------------------
    # Booking actions
    # -------------------------------------------------------------------------

    def action_approved(self):
        for record in self:
            # Do not convert an upcoming Lesson Program session
            # from Booked back to Approved.
            if (
                record.booking_type == "lesson_program"
                and record.lesson_state == "upcoming"
            ):
                record.status = "booked"
            else:
                record.status = "approved"

    def action_refused(self):
        for record in self:
            record.status = "refused"

    # -------------------------------------------------------------------------
    # Cron jobs
    # -------------------------------------------------------------------------

    @api.model
    def mark_completed_bookings(self):
        """Mark past upcoming lessons as completed."""

        now = fields.Datetime.now()

        upcoming_bookings = self.search([
            ("lesson_state", "=", "upcoming"),
            ("availablity_date", "<", now),
        ])

        if upcoming_bookings:
            upcoming_bookings.write({
                "lesson_state": "completed",
            })
            return True

        return False

    @api.model
    def delete_old_draft_bookings(self):
        """Delete past availability slots that remain unbooked."""

        now = fields.Datetime.now()

        old_draft_bookings = self.search([
            ("lesson_state", "=", "draft"),
            ("availablity_date", "<", now),
            ("booking_order_id", "=", False),
        ])

        if old_draft_bookings:
            old_draft_bookings.unlink()
            return True

        return False

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------

    @api.constrains("availablity_date", "booking_id")
    def _check_unique_availability_date(self):
        for record in self:
            if not record.booking_id or not record.availablity_date:
                continue

            existing_booking = self.search(
                [
                    ("availablity_date", "=", record.availablity_date),
                    ("booking_id", "=", record.booking_id.id),
                    ("id", "!=", record.id),
                ],
                limit=1,
            )

            if existing_booking:
                raise ValidationError(
                    _(
                        "The availability date must be unique for the same "
                        "teacher. Teacher %(teacher)s already has a booking "
                        "for this date: %(date)s"
                    )
                    % {
                        "teacher": record.booking_id.name,
                        "date": record.availablity_date,
                    }
                )
