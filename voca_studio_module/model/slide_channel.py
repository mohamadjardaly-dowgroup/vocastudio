# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.osv import expression

from odoo.addons.http_routing.models.ir_http import unslug


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    voca_teacher_id = fields.Many2one('voca.teacher',string='Teacher')
