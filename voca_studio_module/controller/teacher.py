from odoo import http, _, SUPERUSER_ID
from odoo.http import content_disposition, request, Response
import re
from odoo.addons.portal.controllers import portal
from collections import OrderedDict


class TeacherController(http.Controller):

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
    def get_teacher_details(self, **kw):
        try:

            teacher = request.env['voca.teacher'].sudo().search([])
            print("all teacher :",teacher)

            values = {
                'teacher_id': teacher,

            }


            return request.render("voca_studio_module.homepage", values)


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
