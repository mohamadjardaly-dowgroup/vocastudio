# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Voca Module",
    "summary": """ """,
    "version": "0.1",
    "license": "LGPL-3",
    "author": "",
    "website": "",
    "depends": ["base", 'website', 'website_slides', 'mail','website_sale','sale','product','web'],
    "data": [
        'security/ir.model.access.csv',
        'data/teacher_website_menu.xml',
        'view/voca_teacher_view.xml',
        'view/voca_teacher_tags_view.xml',
        'view/voca_teacher_categories_view.xml',
        'view/website_template.xml',
        'view/slide_channel_views.xml',
        'view/appointment_template.xml',
        'view/auth_signup_template.xml',
        'view/portal_template.xml',
        'view/res_partner_views.xml',
        'view/time_slots_views.xml',
        'view/sale_order_views.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'voca_studio_module/static/src/js/time_widget.js',
            'voca_studio_module/static/src/xml/**/*.xml',
            # 'voca_studio_module/static/src/js/website_sale_utils.js',

        ],
        'web.assets_frontend': [
            # 'voca_studio_module/static/src/js/**/*.js',
            #
            'voca_studio_module/static/src/js/bookShow.js',
            'voca_studio_module/static/src/js/selectSeat.js',
            'voca_studio_module/static/src/js/website_sale_utils.js',

            # 'voca_studio_module/static/src/css/show_booking_management.css',
        ],
    },

}
