from odoo import http, _, SUPERUSER_ID
from odoo.http import content_disposition, request, Response
import re
from odoo.addons.portal.controllers import portal
from collections import OrderedDict


class EidOfferController(http.Controller):

    def convert_to_slug(self, display_name):
        # Convert to lowercase
        slug = display_name.lower()
        # Replace spaces with hyphens
        slug = slug.replace(' ', '-')
        # Remove special characters using regex
        slug = re.sub(r'[^a-zA-Z0-9-]', '', slug)
        return slug

    @http.route(['/'], type='http', auth="public",
                methods=['POST', 'GET'], website=True, csrf=False)
    def get_products_by_offer_id(self, offer_id, redirect=None, assets=0, page=1, sortby='SKU', sortby_priority=' asc',
                                 filterby='all', **kw):
        try:
            if assets != 0:
                kw = request.session.get('kw', {})
                page = request.session.get('page', 1)
                sortby = request.session.get('sortby', 'SKU')
                sortby_priority = request.session.get('sortby_priority', ' asc')
                filterby = request.session.get('filterby', 'all')

            password = redirect if redirect else kw.get('password')
            offer_obj = request.env['offer.offer'].sudo().search([('id', '=', offer_id)])

            if offer_obj and (password == offer_obj.password) if offer_obj.password else True:
                domain = [('offer_ids', 'in', [offer_obj.id])]

                searchbar_sortings = {}
                searchbar_sortings['SKU'] = {'label': _('SKU'), 'order': 'sku' + sortby_priority}
                # ' ↑', ' ↓'
                for field_id in offer_obj.sudo().sorting_field_ids:
                    if field_id.name != 'sku':
                        searchbar_sortings[field_id.field_description] = {
                            'label': _(field_id.field_description), 'order': field_id.name + sortby_priority}

                order = searchbar_sortings[sortby]['order']
                searchbar_filters = {
                    'all': {'label': _('All'), 'domain': []},
                }
                domain = searchbar_filters[filterby]['domain'] + domain

                if kw.get('search_product'):
                    search_domain = []
                    search_domain += [('sku', 'ilike', kw.get('search_product'))]
                    for field_id in offer_obj.sudo().search_field_ids:
                        search_domain += [(field_id.name, 'ilike', kw.get('search_product'))]
                    if len(search_domain) > 0:
                        domain += ['|'] * (len(search_domain) - 1) + search_domain

                filters = []
                filters_checkbox = []
                grouped_conditions = {}
                grouped_pricelist = []
                pricelist_items = offer_obj.price_list_id.mapped('item_ids')
                pricelist_domain = []

                for key, value in zip(kw.keys(), kw.values()):
                    if '_checkbox_' in key:
                        field_name = key.split('_checkbox_')[0]
                        field_value = int(key.split('_checkbox_')[1])
                        filters_checkbox.append(key)
                        if field_name not in grouped_conditions:
                            grouped_conditions[field_name] = []

                        if field_name == 'categ_id':
                            grouped_conditions[field_name].append((field_name, 'child_of', [field_value]))
                        else:
                            grouped_conditions[field_name].append((field_name, 'in', [field_value]))

                    if 'filter_' in key:
                        filters.append({key: value})
                        if key.split('filter_')[1] in offer_obj.price_list_id.mapped('name'):
                            grouped_pricelist += ["|"]
                            pricelist_domain += [
                                "&",
                                ("pricelist_id.name", "=", key.split('filter_')[1]),
                                ("fixed_price", "<=", float(value))
                            ]
                        else:
                            domain += [(key.split('filter_')[1], '<=', float(value))]

                for field_name, conditions in grouped_conditions.items():
                    if len(conditions) > 1:
                        domain += ['|'] * (len(conditions) - 1) + conditions
                    else:
                        domain += conditions

                products_temp = request.env['product.template'].sudo().search(domain)
                products_temp_new = request.env['product.template']
                if len(products_temp) > 0 and len(grouped_pricelist) > 0:
                    pricelist_domain = [("product_tmpl_id.offer_ids", "in", [offer_id])] + grouped_pricelist[:-1] + pricelist_domain
                    products_temp_new |= pricelist_items.sudo().search(pricelist_domain).mapped('product_tmpl_id')
                    # print('products_temp_new', products_temp_new, domain)
                    products_temp = products_temp.filtered(lambda curr: curr in products_temp_new)
                    if len(products_temp) > 0:
                        domain += [("id", "in", products_temp.ids)]
                    else:
                        domain += [("id", "=", -1)]

                product_count = len(products_temp)

                # pager
                if 'page_number' in kw.keys() and 'change_page' in kw.keys():
                    page = kw.get('page_number')

                pager = portal.pager(
                    url="/portal/" + str(offer_id),
                    url_args={'sortby': sortby},
                    total=product_count,
                    page=page,
                    step=12
                )

                if 'print_all' in kw.keys():
                    product_ids_obj = request.env['product.template'].sudo().search(domain)
                    if product_ids_obj:
                        current_catalogue = offer_obj.catalogue_id.filtered(
                            lambda new_catalogue: new_catalogue.id == int(kw.get('catalogue_id')))
                        catalogue_wizard_id = request.env['sale.catalogue.wizard'].sudo().create({
                            'name': current_catalogue.name,
                            'image_ids': [
                                (6, 0, current_catalogue.image_ids.ids)] if current_catalogue.image_ids else [],
                            'image_ids2': [
                                (6, 0, current_catalogue.image_ids2.ids)] if current_catalogue.image_ids2 else [],
                            'product_ids': [(6, 0, product_ids_obj.ids)],
                            'field_ids': current_catalogue.sudo().field_ids,
                            'with_extra_media': current_catalogue.with_extra_media,
                            'pricelist_id': current_catalogue.pricelist_id.id
                        })

                        pdf, all_ids = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                            'product_offer.catalogue_sale_order_report_wizard', res_ids=[catalogue_wizard_id.id])
                        pdfhttpheaders = [
                            ('Content-Type', 'application/pdf'),
                            ('Content-Length', u'%s' % len(pdf)),
                            ('Content-Disposition', 'attachment; filename="catalogue.pdf"')
                        ]
                        return request.make_response(pdf, headers=pdfhttpheaders)
                # content according to pager and archive selected

                offer_filtered_price_product_ids = products_temp.sudo().search(domain, order=order, limit=12, offset=pager['offset'])

                # if len(offer_filtered_price_product_ids) > 0 and len(grouped_pricelist) > 0:
                #     print('products_temp_new', products_temp_new, domain, offer_filtered_price_product_ids)
                #     offer_filtered_price_product_ids = offer_filtered_price_product_ids.filtered(lambda curr_pro: curr_pro in products_temp_new)

                # products = product_ids.ids if product_ids else []
                product_ids_list = ''

                for product in self.get_price_from_offer(offer_obj, offer_filtered_price_product_ids, 'product'):
                    product_ids_list += str(product.get('product_id')) + '-'

                # offer_filtered_price_product_ids = product_ids.filtered(
                #     lambda line: line in products if len(products) > 0 else 1 == 1)

                values = {
                    'offer_id': offer_obj,
                    'product_ids': offer_filtered_price_product_ids,
                    'products_ids_prices': self.get_price_from_offer(offer_obj, offer_filtered_price_product_ids,
                                                                     'product'),
                    'selected_products': kw.get(
                        'edited_new_product_ids_list') if 'edited_new_product_ids_list' in kw.keys() else None,
                    'product_ids_list': product_ids_list.rstrip("-"),
                    'page_name': 'offer_page',
                    'default_url': '/portal/' + str(offer_id),
                    'pager': pager,
                    'curr_page': page,
                    'searchbar_sortings': searchbar_sortings,
                    'sortby': sortby,
                    'sortby_priority': sortby_priority,
                    'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
                    'search_result': kw.get('search_product'),
                    'filterby': filterby,
                    'filters': filters,
                    'filters_checkbox': filters_checkbox,
                    'add_to_pdf_checkboxes': kw.keys(),
                    'total': product_count,
                    'password': password if password else 'None',
                    'assets': assets
                }

                request.session['kw'] = kw
                request.session['sortby'] = sortby
                request.session['sortby_priority'] = sortby_priority
                request.session['filterby'] = filterby

                return request.render("product_offer.product_offer_details_page", values)

            elif offer_obj and password != offer_obj.password and password is not None:
                # Password is incorrect or offer not found, render the password check page with an error message
                error_message = 'Incorrect password' if offer_obj else 'Portal not found'
                return http.request.render('product_offer.password_page',
                                           {'error_message': error_message, 'offer_id': offer_id})

            else:
                return http.request.render('product_offer.password_page', {'offer_id': offer_id})

        except Exception as e:
            return e

    def get_price_from_offer(self, offer, product_ids, group_by='price_list'):
        result = []
        if group_by == 'product':
            for product in product_ids:
                res = []
                for price_list in offer.price_list_id:
                    price = 0
                    try:
                        price = price_list.sudo()._compute_price_rule(products=product, quantity=1,
                                                                      uom=product.uom_id)
                    except:
                        pass

                    res.append({
                        'pricelist_id': price_list.id,
                        'pricelist': price_list.name,
                        'price': next(iter(price.values()))[0] if price else product.list_price,
                        'currency_id': price_list.currency_id.symbol
                    })

                result.append({
                    'product_id': product.id,
                    'prices': res
                })
        else:
            for price_list in offer.price_list_id:
                res = []
                for product in product_ids.filtered(
                        lambda product_id: product_id.id in price_list.item_ids.mapped('product_tmpl_id').ids):
                    price = 0
                    try:
                        price = price_list.sudo()._compute_price_rule(products=product, quantity=1,
                                                                      uom=product.uom_id)
                    except:
                        pass

                    res.append({
                        'product_id': product.id,
                        'price': next(iter(price.values()))[0] if price else product.list_price,
                    })

                result.append({
                    'pricelist_id': price_list.id,
                    'pricelist': price_list.name,
                    'currency_id': price_list.currency_id.symbol,
                    'product_ids': res
                })
        return result

    @http.route('/portal/<int:offer_id>/product/<int:productid>', type='http', auth="public", methods=['GET'],
                website=True, csrf=False)
    def redirect_to_product_by_offer(self, offer_id, productid, redirect=None, **kw):
        if not redirect:
            return http.request.redirect('/portal/' + str(offer_id))
        else:
            offer_obj = request.env['offer.offer'].sudo().search([('id', '=', offer_id)])
            product_id = request.env['product.template'].sudo().search([('id', '=', productid)], limit=1)
            return request.render("product_offer.product_offer_form_page", {
                'offer_id': offer_obj,
                'product_id': product_id,
                'products_id_prices': self.get_price_from_offer(offer_obj, product_id, 'product'),
                'redirect': redirect,
                'page_name': 'offer_product_form'
            })

    @http.route('/portal/<int:offer_id>/product/print/catalogue/<int:catalogue>', type='http', auth="public",
                methods=['GET'], website=True, csrf=False)
    def print_offer_product_catalogue(self, offer_id, catalogue, product_ids=None, redirect=None, **kw):
        offer_obj = request.env['offer.offer'].sudo().search([('id', '=', offer_id)])

        if offer_obj.password:
            if not redirect or request.env['offer.offer'].sudo().search_count(
                    [('id', '=', offer_id), ('password', '=', redirect)]) == 0:
                return http.request.redirect('/portal/' + str(offer_id))

        product_ids_obj = request.env['product.template'].sudo().search(
            [('id', 'in', product_ids.rstrip("-").split('-') if product_ids else []),
             ('offer_ids', 'in', [offer_id])])
        if product_ids_obj:
            current_catalogue = offer_obj.catalogue_id.filtered(lambda new_catalogue: new_catalogue.id == catalogue)
            catalogue_wizard_id = request.env['sale.catalogue.wizard'].sudo().create({
                'name': current_catalogue.name,
                'image_ids': [
                    (6, 0, current_catalogue.image_ids.ids)] if current_catalogue.image_ids else [],
                'image_ids2': [
                    (6, 0, current_catalogue.image_ids2.ids)] if current_catalogue.image_ids2 else [],
                'product_ids': [(6, 0, product_ids_obj.ids)],
                'field_ids': current_catalogue.sudo().field_ids,
                'with_extra_media': current_catalogue.with_extra_media,
                'pricelist_id': current_catalogue.pricelist_id.id
            })

            pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'product_offer.catalogue_sale_order_report_wizard', res_ids=[catalogue_wizard_id.id])
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', u'%s' % len(pdf)),
                ('Content-Disposition', 'attachment; filename="catalogue.pdf"')
            ]
            return request.make_response(pdf, headers=pdfhttpheaders)

        else:
            return http.request.redirect('/portal/' + str(offer_id))
