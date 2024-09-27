# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Voca Module",
    "summary": """ """,
    "version": "0.1",
    "license": "LGPL-3",
    "author": "",
    "website": "",
    "depends": ["base", 'website','website_slides' ],
    "data": [
        'security/ir.model.access.csv',
        'data/teacher_website_menu.xml',
        'view/voca_teacher_view.xml',
        'view/voca_teacher_tags_view.xml',
        'view/voca_teacher_categories_view.xml',
        'view/website_template.xml',
        'view/slide_channel_views.xml',
        'view/website_slides_templates_course.xml',
        'view/appointment_template.xml',
        'view/auth_signup_template.xml',
        'view/portal_template.xml',
        # 'view/res_partner_views.xml',

    ],


}
