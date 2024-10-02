import datetime
import logging
from odoo import api, fields, models, tools, _

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo.addons.http_routing.models.ir_http import slug

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'website.searchable.mixin', ]
    # from avatar.mixin

    is_teacher = fields.Boolean(string=_('Is Teacher'), default=True)
    first_name = fields.Char(string=_('First Name'), translate=True, tracking=True)
    nickname = fields.Char(string=_('Nickname'), translate=True, tracking=True)
    gender = fields.Selection(
        selection=[('male', _('Male')),
         ('female', _('Female'))])
    gender_1 = fields.Selection(
        selection=[('male', _('Male')),
         ('female', _('Female'))])
    birthday = fields.Date(string=_('Birth Day'))
    age = fields.Integer(string=_("age"), compute='_compute_age')
    role = fields.Selection(
        selection=[('teacher', _('Teacher')),
                   ('student', _('Student'))])

    experience = fields.Char(string=_('Experience'), translate=True, tracking=True)
    about = fields.Char(string=_('About'), translate=True, tracking=True)

    tag_ids = fields.Many2many('voca.teacher.tags', string='Tags')
    category_ids = fields.Many2many('voca.teacher.categories',string='Category')
    attachment_ids = fields.Many2many('ir.attachment')

    image_base64 = fields.Image(string="Image", readonly=False)


    teacher_id = fields.Many2one('voca.teacher', string='Teacher')


    @api.depends('birthday')
    def _compute_age(self):
        # today = datetime.now().date()
        # current_year = fields.Date.today().year
        today = fields.Date.today()
        for record in self:
            if record.birthday:
                # birth_date = datetime.strptime(record.birthday, "%Y-%m-%d").date()
                age = relativedelta(today, record.birthday).years
                record.age = age
            else:
                record.age = 0

    @api.model_create_multi
    def create(self, values):
        print("on createeeeeeeeeeeee")
        partners = super(ResPartner, self).create(values)
        for value, partner in zip(values, partners):
            if value.get('role') == 'teacher':
                # Create the voca.teacher record
                x = self.env['voca.teacher'].sudo().create({
                    'instructor': partner.id,
                    'experience': value.get('experience', ''),  # Get experience from value if exists
                    'state': 'draft',
                })

                partner.sudo().write({
                    'teacher_id': x.id
                })
                rec_id = self.env['ir.model'].sudo().search([('model', '=', 'voca.teacher')], limit=1)
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': 4,
                    'date_deadline': date.today(),
                    'summary': 'Request to approve',
                    'user_id': 2,
                    'res_model_id': rec_id.id,
                    'res_id': x.id
                })

        return partners


