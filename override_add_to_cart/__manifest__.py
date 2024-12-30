{
    'name': 'Override Add to Cart',
    'category': 'Hidden',
    'version': '0.1',
    'depends': ['website_sale'],
    'data': [

    ],
    'demo': [
    ],
    'assets': {
        'web.assets_frontend': [
            ('prepend', 'override_add_to_cart/static/src/js/*.js'),
        ],
    },
    'auto_install': True,
}
