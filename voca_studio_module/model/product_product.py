from odoo import _, api, fields, models



class Product(models.Model):
    _inherit = 'product.product'

    is_master = fields.Boolean(string='Is Master')
    
    #samiha##########################################################
    master_class_id = fields.Many2one('master.classes', string='Master Class')

class Product(models.Model):
    _inherit = 'product.template'

    is_master = fields.Boolean(string='Is Master')


