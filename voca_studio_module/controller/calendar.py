from odoo import http
from odoo.http import request

class PortalCalendar(http.Controller):

    @http.route('/my/calendar', type='http', auth='user', website=True)
    def portal_my_calendar(self, **kw):
        
        user = request.env.user
        print("user calendar .............: ", user)   
        # Fetch events where the user is an attendee
        attendee_events = request.env['calendar.event'].sudo().search([
            ('attendee_ids.partner_id', '=', user.partner_id.id)
        ])
        values = {
            'events': attendee_events,
        }
        return request.render('calendar_portal_dashboard.portal_dashboard_calendar_events', values)
