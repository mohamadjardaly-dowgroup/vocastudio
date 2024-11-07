from odoo import _, api, fields, models



class Product(models.Model):
    _inherit = 'product.product'

    is_master = fields.Boolean(string='Is Master')

class Product(models.Model):
    _inherit = 'product.template'

    is_master = fields.Boolean(string='Is Master')


