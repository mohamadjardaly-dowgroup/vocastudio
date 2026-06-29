from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class VocaLessonProgram(models.Model):
    _name = "voca.lesson.program"
    _description = "Lesson Program"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Lesson Title", required=True, tracking=True)

    teacher_id = fields.Many2one(
        "voca.teacher",
        string="Teacher",
        required=True,
        tracking=True,
    )

    image_1920 = fields.Image(string="Cover Image")

    description = fields.Text(string="Short Description")
    description_html = fields.Html(string="Full Description")

    session_count = fields.Integer(
        string="Number of Lessons",
        required=True,
        default=5,
        tracking=True,
    )

    duration = fields.Integer(
        string="Lesson Duration (minutes)",
        related="teacher_id.duration",
        readonly=True,
    )

    price = fields.Monetary(
        string="Price",
        required=True,
        tracking=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Related Product",
        readonly=True,
        copy=False,
    )

    active = fields.Boolean(default=True)

    is_published = fields.Boolean(
        string="Published on Website",
        default=True,
        tracking=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("published", "Published"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="published",
        tracking=True,
    )

    _sql_constraints = [
        (
            "check_positive_session_count",
            "CHECK(session_count > 0)",
            "Number of lessons must be greater than zero.",
        ),
        (
            "check_positive_price",
            "CHECK(price > 0)",
            "Price must be greater than zero.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        programs = super().create(vals_list)

        for program in programs:
            if not program.product_id:
                product = self.env["product.product"].sudo().create({
                    "name": "%s - Lesson Program" % program.name,
                    "type": "service",
                    "is_published": True,
                    "list_price": program.price,
                    "image_1920": program.image_1920,
                })
                program.product_id = product.id

        return programs

    def write(self, vals):
        res = super().write(vals)

        for program in self:
            if program.product_id:
                product_vals = {}

                if "name" in vals:
                    product_vals["name"] = "%s - Lesson Program" % program.name

                if "price" in vals:
                    product_vals["list_price"] = program.price

                if "image_1920" in vals:
                    product_vals["image_1920"] = program.image_1920

                if "is_published" in vals:
                    product_vals["is_published"] = program.is_published

                if product_vals:
                    program.product_id.sudo().write(product_vals)

        return res

    @api.constrains("teacher_id")
    def _check_teacher_approved(self):
        for program in self:
            if program.teacher_id and program.teacher_id.state != "approved":
                raise ValidationError(_("You can only publish lesson programs for approved teachers."))