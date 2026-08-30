from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    package_ids = fields.One2many(
        comodel_name='voca.teacher.packaging.lines',
        inverse_name='product_id',
        string='Packages',
    )

    # @api.model
    # def _get_combination_info(self, combination, add_qty=1, **kwargs):
    #     print("Current context in _get_combination_info:>>>>>>>>>>>>>>>>>>>", self.env.context)
    #     package_id = self.env.context.get('package_id')
    #     print("I am inside _get_combination_info: package_id >>>>>>>>>>>>", package_id)
    #     if package_id:
    #         package = self.env['voca.teacher.packaging.lines'].sudo().browse(package_id)
    #         if package:
    #             add_qty = package.quantity  # Override add_qty with package quantity
    #             print(f"Package Quantity (add_qty) >>>>>>>>>> {add_qty}")

    #     # Call the super method with the updated add_qty
    #     result = super()._get_combination_info(combination, add_qty=add_qty, **kwargs)
    #     result['add_qty'] = add_qty  # Include the quantity in the result
    #     return result
