import json
import logging
from datetime import datetime

import pytz

from odoo import http, fields
from odoo.http import request
from odoo.tools import format_amount


_logger = logging.getLogger(__name__)


class LessonProgramController(http.Controller):

    def _to_user_datetime(self, dt, tz_name):
        if not dt:
            return False

        tz_name = tz_name or "UTC"
        user_tz = pytz.timezone(tz_name)

        if dt.tzinfo:
            utc_dt = dt.astimezone(pytz.UTC)
        else:
            utc_dt = pytz.UTC.localize(dt)

        return utc_dt.astimezone(user_tz)

    @http.route("/lessons", type="http", auth="public", website=True)
    def lesson_programs(self, **kw):
        programs = request.env["voca.lesson.program"].sudo().search([
            ("active", "=", True),
            ("is_published", "=", True),
            ("state", "=", "published"),
            ("teacher_id.state", "=", "approved"),
        ], order="id desc")

        pricelist = request.website._get_current_pricelist()

        return request.render("voca_studio_module.lesson_program_list_template", {
            "programs": programs,
            "currency_id": pricelist.currency_id,
            "format_amount": lambda amount, currency: format_amount(request.env, amount, currency),
        })

    @http.route("/lesson-program/<int:program_id>", type="http", auth="public", website=True)
    def lesson_program_detail(self, program_id, **kw):
        if request.env.user._is_public():
            return request.redirect("/web/login?redirect=/lesson-program/%s" % program_id)

        program = request.env["voca.lesson.program"].sudo().browse(program_id)
        if not program.exists() or not program.is_published or program.state != "published":
            return request.not_found()

        if program.teacher_id.state != "approved":
            return request.not_found()

        pricelist = request.website._get_current_pricelist()

        program_currency = program.currency_id
        program_price = program.price

        if program_currency != pricelist.currency_id:
            converted_price = program_currency._convert(
                from_amount=program_price,
                to_currency=pricelist.currency_id,
                company=request.env.company,
                date=fields.Date.today(),
            )
        else:
            converted_price = program_price

        return request.render("voca_studio_module.lesson_program_booking_template", {
            "program": program,
            "teacher": program.teacher_id,
            "product": program.product_id,
            "session_count": program.session_count,
            "converted_price": converted_price,
            "currency_id": pricelist.currency_id,
            "format_amount": lambda amount, currency: format_amount(request.env, amount, currency),
        })

    @http.route("/lesson_program/available_dates", type="http", auth="user", website=True)
    def lesson_program_available_dates(self, program_id, date=None, **kw):
        program = request.env["voca.lesson.program"].sudo().browse(int(program_id))
        if not program.exists():
            return request.make_response(
                json.dumps({}),
                headers=[("Content-Type", "application/json")]
            )

        user_tz_name = request.env.user.tz or "UTC"
        user_tz = pytz.timezone(user_tz_name)

        teacher = program.teacher_id
        bookings_by_day = {}

        booking_lines = teacher.booking_ids.filtered(
            lambda b: (
                b.status == "approved"
                and b.lesson_state == "draft"
                and not b.booking_order_id
            )
        )

        for book in booking_lines:
            avail_date = book.availablity_date

            if isinstance(avail_date, str):
                avail_date = datetime.strptime(avail_date, "%Y-%m-%d %H:%M:%S")

            local_dt = pytz.UTC.localize(avail_date).astimezone(user_tz)
            day_key = local_dt.strftime("%Y-%m-%d")

            bookings_by_day.setdefault(day_key, []).append({
                "time": local_dt.strftime("%I:%M %p"),
                "booking_id": book.id,
                "status": book.status,
            })

        if date:
            result = bookings_by_day.get(date, [])
        else:
            result = bookings_by_day

        return request.make_response(
            json.dumps(result),
            headers=[("Content-Type", "application/json")]
        )

    @http.route("/lesson_program/available_times", type="http", auth="user", website=True)
    def lesson_program_available_times(self, program_id, date, **kw):
        program = request.env["voca.lesson.program"].sudo().browse(int(program_id))
        if not program.exists():
            return request.make_response(
                json.dumps([]),
                headers=[("Content-Type", "application/json")]
            )

        user_tz_name = request.env.user.tz or "UTC"
        user_tz = pytz.timezone(user_tz_name)

        teacher = program.teacher_id
        time_slots = []

        booking_lines = teacher.booking_ids.filtered(
            lambda b: (
                b.status == "approved"
                and b.lesson_state == "draft"
                and not b.booking_order_id
            )
        )

        for book in booking_lines:
            avail_date = book.availablity_date

            if isinstance(avail_date, str):
                avail_date = datetime.strptime(avail_date, "%Y-%m-%d %H:%M:%S")

            local_dt = pytz.UTC.localize(avail_date).astimezone(user_tz)

            if local_dt.strftime("%Y-%m-%d") != date:
                continue

            time_slots.append({
                "time": local_dt.strftime("%I:%M %p"),
                "datetime": local_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "booking_id": book.id,
                "status": book.status,
            })

        time_slots.sort(key=lambda x: datetime.strptime(x["time"], "%I:%M %p"))

        return request.make_response(
            json.dumps(time_slots),
            headers=[("Content-Type", "application/json")]
        )

    @http.route(
        "/custom/update_lesson_program_order_line",
        type="http",
        auth="user",
        website=True,
        csrf=False,
        methods=["POST"],
    )
    def update_lesson_program_order_line(self, **kwargs):
        program_id = kwargs.get("program_id")
        selected_booking_ids = kwargs.get("selected_booking_ids")

        if not program_id or not selected_booking_ids:
            return request.make_response(
                json.dumps({"error": "Missing required parameters"}),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        program = request.env["voca.lesson.program"].sudo().browse(int(program_id))
        if not program.exists():
            return request.make_response(
                json.dumps({"error": "Lesson program not found"}),
                headers=[("Content-Type", "application/json")],
                status=404,
            )

        try:
            selected_ids = json.loads(selected_booking_ids)
        except Exception:
            selected_ids = []

        selected_ids = [int(x) for x in selected_ids if x]

        if len(selected_ids) != program.session_count:
            return request.make_response(
                json.dumps({
                    "error": "You must select exactly %s lesson times." % program.session_count
                }),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        booking_lines = request.env["voca.teacher.booking.lines"].sudo().browse(selected_ids).exists()

        if len(booking_lines) != program.session_count:
            return request.make_response(
                json.dumps({"error": "Some selected times are no longer available."}),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        invalid_lines = booking_lines.filtered(
            lambda b: (
                b.booking_id.id != program.teacher_id.id
                or b.status != "approved"
                or b.lesson_state != "draft"
                or b.booking_order_id
            )
        )

        if invalid_lines:
            return request.make_response(
                json.dumps({"error": "Some selected times are already booked or unavailable."}),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        sale_order = request.website.sale_get_order(force_create=True)

        pricelist = request.website._get_current_pricelist()
        program_currency = program.currency_id
        program_price = program.price

        if program_currency != pricelist.currency_id:
            converted_price = program_currency._convert(
                from_amount=program_price,
                to_currency=pricelist.currency_id,
                company=request.env.company,
                date=fields.Date.today(),
            )
        else:
            converted_price = program_price

        description_lines = []
        user_tz_name = request.env.user.tz or "UTC"

        for booking in booking_lines.sorted("availablity_date"):
            local_dt = self._to_user_datetime(booking.availablity_date, user_tz_name)
            description_lines.append(local_dt.strftime("%d %B %Y, %I:%M %p"))

        description = "%s\nSelected Times:\n%s" % (
            program.name,
            "\n".join(description_lines),
        )

        order_line = request.env["sale.order.line"].sudo().search([
            ("order_id", "=", sale_order.id),
            ("lesson_program_id", "=", program.id),
        ], limit=1)
        
        unit_price = converted_price / program.session_count

        line_vals = {
            "product_id": program.product_id.id,
            "product_uom_qty": program.session_count,
            "converted_price": converted_price,
            "price_unit": unit_price,
            "name": description,
            "lesson_program_id": program.id,
            "product_uom": program.product_id.uom_id.id,
            "tax_id": [(6, 0, program.product_id.taxes_id.ids)],
            "booking_ids": [(6, 0, booking_lines.ids)],
        }

        if order_line:
            order_line.write(line_vals)
        else:
            sale_order.sudo().write({
                "order_line": [(0, 0, line_vals)]
            })

            # After creating the line through sale_order.write(),
            # fetch the newly created sale order line.
            order_line = request.env["sale.order.line"].sudo().search([
                ("order_id", "=", sale_order.id),
                ("lesson_program_id", "=", program.id),
            ], limit=1)

        # Link the selected calendar slots to the sale order line.
        # This makes line.booking_ids work in the dashboards.
        if order_line:
            booking_lines.write({
                "booking_order_id": order_line.id,
                "booking_type": "lesson_program",
                "lesson_program_id": program.id,
            })

        return request.make_response(
            json.dumps({"success": True, "redirect": "/shop/cart"}),
            headers=[("Content-Type", "application/json")]
        )


class StudentLessonProgramDashboard(http.Controller):

    def _localize(self, dt, tz_name):
        if not dt:
            return ""

        tz_name = tz_name or "UTC"
        user_tz = pytz.timezone(tz_name)

        if dt.tzinfo:
            utc_dt = dt.astimezone(pytz.UTC)
        else:
            utc_dt = pytz.UTC.localize(dt)

        return utc_dt.astimezone(user_tz).strftime("%d %B %Y, %I:%M %p")

    @http.route("/my_dashboard/lesson-programs", type="http", auth="user", website=True)
    def my_lesson_programs(self, page=1, limit=10, **kwargs):
        try:
            page = int(page)
        except Exception:
            page = 1

        student = request.env.user.partner_id
        user_tz_name = request.env.user.tz or student.tz or "UTC"

        # Search sale order lines first.
        # This is more reliable because the lesson program is stored on the order line.
        order_lines = request.env["sale.order.line"].sudo().search([
            ("order_id.partner_id", "=", student.id),
            ("order_id.state", "in", ["sale", "done", "sent"]),
            ("lesson_program_id", "!=", False),
        ], order="id desc")

        grouped_list = []

        for line in order_lines:
            sessions = []

            bookings = line.booking_ids.filtered(
                lambda b: b.lesson_state in ["draft", "upcoming"]
            ).sorted("availablity_date")

            for booking in bookings:
                sessions.append({
                    "booking": booking,
                    "local_date": self._localize(booking.availablity_date, user_tz_name),
                })

            grouped_list.append({
                "line": line,
                "program": line.lesson_program_id,
                "teacher": line.lesson_program_id.teacher_id if line.lesson_program_id else False,
                "sessions": sessions,
            })

        total = len(grouped_list)
        total_pages = (total + limit - 1) // limit if limit else 1
        offset = (page - 1) * limit
        paginated = grouped_list[offset:offset + limit]

        return request.render("voca_studio_module.student_lesson_programs_partial", {
            "lesson_programs": paginated,
            "page": page,
            "total_pages": total_pages,
        })
        
class TeacherLessonProgramDashboard(http.Controller):

    def _localize(self, dt, tz_name):
        if not dt:
            return ""

        tz_name = tz_name or "UTC"
        user_tz = pytz.timezone(tz_name)

        if dt.tzinfo:
            utc_dt = dt.astimezone(pytz.UTC)
        else:
            utc_dt = pytz.UTC.localize(dt)

        return utc_dt.astimezone(user_tz).strftime("%d %B %Y, %I:%M %p")

    @http.route("/teacher_dashboard/lesson-programs", type="http", auth="user", website=True)
    def teacher_lesson_programs(self, page=1, limit=10, **kwargs):
        try:
            page = int(page)
        except Exception:
            page = 1

        teacher_partner = request.env.user.partner_id
        teacher = teacher_partner.teacher_id

        if not teacher:
            return request.render("voca_studio_module.teacher_lesson_programs_partial", {
                "lesson_programs": [],
                "page": 1,
                "total_pages": 1,
            })

        user_tz_name = request.env.user.tz or "UTC"

        # Search sale order lines first.
        # This is safer because lesson_program_id is stored on the order line.
        order_lines = request.env["sale.order.line"].sudo().search([
            ("order_id.state", "in", ["sale", "done", "sent"]),
            ("lesson_program_id", "!=", False),
            ("lesson_program_id.teacher_id", "=", teacher.id),
        ], order="id desc")

        grouped_list = []

        for line in order_lines:
            sessions = []

            bookings = line.booking_ids.filtered(
                lambda b: b.lesson_state in ["draft", "upcoming"]
            ).sorted("availablity_date")

            for booking in bookings:
                sessions.append({
                    "booking": booking,
                    "local_date": self._localize(booking.availablity_date, user_tz_name),
                })

            grouped_list.append({
                "line": line,
                "program": line.lesson_program_id,
                "student": line.order_id.partner_id,
                "sessions": sessions,
            })

        total = len(grouped_list)
        total_pages = (total + limit - 1) // limit if limit else 1
        offset = (page - 1) * limit
        paginated = grouped_list[offset:offset + limit]

        return request.render("voca_studio_module.teacher_lesson_programs_partial", {
            "lesson_programs": paginated,
            "page": page,
            "total_pages": total_pages,
        })