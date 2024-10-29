///** @odoo-module **/
//
//import { cartHandlerMixin } from '@website_sale/js/website_sale_utils';
//import { patch } from "@web/core/utils/patch";
//
//patch(cartHandlerMixin, {
//    /**
//     * Override to disable the datimepicker as soon as rental product is added to cart.
//     * @override
//     */
//    async _addToCartInPage(params) {
//    console.log('eeeeeee');
//        const data = await super._addToCartInPage(...arguments);
//        return wUtils.sendRequest('/shop/checkout', {"express": "1"});
//
//    },
//});
//
//





///** @odoo-module **/
////import { cartHandlerMixin } from '@website_sale/js/website_sale_utils';
//import publicWidget from '@web/legacy/js/public/public_widget';
//import { cartHandlerMixin } from '@website_sale/js/website_sale_utils';
//import { WebsiteSale } from '@website_sale/js/website_sale';
//import { patch } from "@web/core/utils/patch";
//
//patch(cartHandlerMixin, {
//
//    addToCart(params) {
//            const data =  super.addToCart(...arguments);
//
//    console.info('hello');
//        if (this.isBuyNow) {
//            params.express = true;
//        } else if (this.stayOnPageOption) {
//            this._addToCartInPage(params);
//            return wUtils.sendRequest('/shop/checkout', {"express": "1"});
//        }
//        return wUtils.sendRequest('/shop/cart/update', params);
//    },
//});



//
///** @odoo-module **/
//
//import publicWidget from '@web/legacy/js/public/public_widget';
//import { cartHandlerMixin } from '@website_sale/js/website_sale_utils';
//import { WebsiteSale } from '@website_sale/js/website_sale';
//import { _t } from "@web/core/l10n/translation";
//
//// Extend the original widget
//publicWidget.registry.AddToCartSnippet = WebsiteSale.extend(cartHandlerMixin, {
//
//    /**
//     * Override the addToCart function.
//     */
//    addToCart(params) {
//        console.info('hello');
//            if (this.isBuyNow) {
//                params.express = true;
//            } else if (this.stayOnPageOption) {
//                this._addToCartInPage(params);
//                return wUtils.sendRequest('/shop/checkout', {"express": "1"});
//            }
//            return wUtils.sendRequest('/shop/cart/update', params);
//    },});
//
//export default publicWidget.registry.AddToCartSnippet;
