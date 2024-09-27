import datetime
import logging
from odoo import api, fields, models, tools, _
from dateutil.relativedelta import relativedelta

from odoo.addons.http_routing.models.ir_http import slug

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'website.searchable.mixin', ]

    _description = "alumni model"
    # from avatar.mixin

    is_teacher = fields.Boolean(string=_('Is Teacher'), default=False)
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
        partner = super(ResPartner, self).create(values)
        for value in values :
            print("Ssssssssssssss",value)
            if value['role'] == 'teacher':
                self.env['voca.teacher'].sudo().create({

                    'instructor': partner.id,
                    'experience': partner.experience,

                })
        return partner


