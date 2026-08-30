/** @odoo-module **/

import { cartHandlerMixin } from '@website_sale/js/website_sale_utils';
import { patch } from "@web/core/utils/patch";
import wUtils from '@website/js/utils';


patch(cartHandlerMixin, {

     addToCart(params) {
     const data =  super.addToCart(...arguments);

    console.info('hello');
        if (this.isBuyNow) {
            params.express = true;
        } else if (this.stayOnPageOption) {
            this._addToCartInPage(params);
            return wUtils.sendRequest('/shop/cart',params);
        }
        return wUtils.sendRequest('/shop/cart/update', params);
    },
});
