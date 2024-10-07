# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.osv import expression

from odoo.addons.http_routing.models.ir_http import unslug


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    package_id = fields.Many2one('voca.teacher.packaging.lines',string='Teacher package')

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    booking_ids= fields.One2many('voca.teacher.booking.lines', 'booking_order_id', string='Booking')

