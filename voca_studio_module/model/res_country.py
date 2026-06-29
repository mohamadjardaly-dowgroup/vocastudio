import phonenumbers
from odoo import models, fields, api

class ResCountry(models.Model):
    _inherit = "res.country"

    dialing_code = fields.Char(string="Dialing Code", compute="_compute_dialing_code", store=True)

    @api.depends("code")
    def _compute_dialing_code(self):
        """Automatically fetch the dialing code based on country ISO code."""
        for record in self:
            try:
                if record.code:
                    record.dialing_code = phonenumbers.country_code_for_region(record.code)
                else:
                    record.dialing_code = ""
            except Exception:
                record.dialing_code = ""
