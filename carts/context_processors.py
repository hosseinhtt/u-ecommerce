from carts.models import Cart, CartItem
from carts.views import CartMixin

def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return{}
    else:
        try:
            cart_mixin = CartMixin()
            cart_id = cart_mixin._cart_id(request)
            
            cart = Cart.objects.filter(cart_id=cart_id)
            cart_items = CartItem.objects.all().filter(cart=cart[:1])
            for cart_item in cart_items:
                cart_count += cart_item.quantity

        except Cart.DoesNotExist:
            cart_count = 0
    return dict(cart_count=cart_count)