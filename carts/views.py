from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator
from django.http import HttpResponse



class CartMixin:
    def _cart_id(self, request):
        cart = request.session.session_key
        if not cart:
            cart = request.session.create()
        return cart

class CartView(View, CartMixin):
    def get(self, request, total=0, quantity=0, cart_items=None):
        try:
            tax = 0
            grand_total = 0
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user, is_active=True)
            else:
                cart = Cart.objects.get(cart_id=self._cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            for cart_item in cart_items:
                total += (cart_item.product.price * cart_item.quantity)
                quantity += cart_item.quantity
            tax = (2 * total) / 100
            grand_total = total + tax
        except ObjectDoesNotExist:
            pass  # just ignore

        context = {
            'total': total,
            'quantity': quantity,
            'cart_items': cart_items,
            'tax': tax,
            'grand_total': grand_total,
        }
        return render(request, 'store/cart.html', context)

class CheckoutView(View, CartMixin):
    @method_decorator(login_required(login_url='accounts:login'))
    def get(self, request, total=0, quantity=0, cart_items=None):
        try:
            tax = 0
            grand_total = 0
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user, is_active=True)
            else:
                cart = Cart.objects.get(cart_id=self._cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            for cart_item in cart_items:
                total += (cart_item.product.price * cart_item.quantity)
                quantity += cart_item.quantity
            tax = (2 * total) / 100
            grand_total = total + tax
        except ObjectDoesNotExist:
            pass  # just ignore

        context = {
            'total': total,
            'quantity': quantity,
            'cart_items': cart_items,
            'tax': tax,
            'grand_total': grand_total,
        }
        return render(request, 'store/checkout.html', context)
class AddToCartView(View, CartMixin):
    def post(self, request, product_id):
        current_user = request.user
        product = Product.objects.get(id=product_id)  # get the product
        # If the user is authenticated
        if current_user.is_authenticated:
            product_variation = []
            if request.method == 'POST':
                for item in request.POST:
                    key = item
                    value = request.POST[key]

                    try:
                        variation = Variation.objects.get(product=product, variation_category__iexact=key,
                                                         variation_value__iexact=value)
                        product_variation.append(variation)
                    except:
                        pass

            is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
            if is_cart_item_exists:
                cart_item = CartItem.objects.filter(product=product, user=current_user)
                ex_var_list = []
                id = []
                for item in cart_item:
                    existing_variation = item.variations.all()
                    ex_var_list.append(list(existing_variation))
                    id.append(item.id)

                if product_variation in ex_var_list:
                    # increase the cart item quantity
                    index = ex_var_list.index(product_variation)
                    item_id = id[index]
                    item = CartItem.objects.get(product=product, id=item_id)
                    item.quantity += 1
                    item.save()

                else:
                    item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                    if len(product_variation) > 0:
                        item.variations.clear()
                        item.variations.add(*product_variation)
                    item.save()
            else:
                cart_item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    user=current_user,
                )
                if len(product_variation) > 0:
                    cart_item.variations.clear()
                    cart_item.variations.add(*product_variation)
                cart_item.save()
            return redirect('carts:cart')
        # If the user is not authenticated
        else:
            product_variation = []
            if request.method == 'POST':
                for item in request.POST:
                    key = item
                    value = request.POST[key]

                    try:
                        variation = Variation.objects.get(product=product, variation_category__iexact=key,
                                                         variation_value__iexact=value)
                        product_variation.append(variation)
                    except:
                        pass

            try:
                cart = Cart.objects.get(cart_id=self._cart_id(request))  # get the cart using the cart_id present in the session
            except Cart.DoesNotExist:
                cart = Cart.objects.create(
                    cart_id=self._cart_id(request)
                )
            cart.save()

            is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
            if is_cart_item_exists:
                cart_item = CartItem.objects.filter(product=product, cart=cart)
                # existing_variations -> database
                # current variation -> product_variation
                # item_id -> database
                ex_var_list = []
                id = []
                for item in cart_item:
                    existing_variation = item.variations.all()
                    ex_var_list.append(list(existing_variation))
                    id.append(item.id)

                print(ex_var_list)

                if product_variation in ex_var_list:
                    # increase the cart item quantity
                    index = ex_var_list.index(product_variation)
                    item_id = id[index]
                    item = CartItem.objects.get(product=product, id=item_id)
                    item.quantity += 1
                    item.save()

                else:
                    item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                    if len(product_variation) > 0:
                        item.variations.clear()
                        item.variations.add(*product_variation)
                    item.save()
            else:
                cart_item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    cart=cart,
                )
                if len(product_variation) > 0:
                    cart_item.variations.clear()
                    cart_item.variations.add(*product_variation)
                cart_item.save()
            return redirect('carts:cart')

class RemoveCartView(View):
    def get(self, request, product_id, cart_item_id):
        product = get_object_or_404(Product, id=product_id)
        try:
            if request.user.is_authenticated:
                cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
            else:
                cart_mixin = CartMixin()
                cart_id = cart_mixin._cart_id(request)
                cart = Cart.objects.get(cart_id=cart_id)
                cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
        except:
            pass
        return redirect('carts:cart')

class RemoveCartItemView(View):
    def get(self, request, product_id, cart_item_id):
        product = get_object_or_404(Product, id=product_id)
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart_mixin = CartMixin()
            cart_id = cart_mixin._cart_id(request)
            cart = Cart.objects.get(cart_id=cart_id)
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item.delete()
        return redirect('carts:cart')










# #viewset

# from rest_framework import status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.viewsets import ModelViewSet
# from .models import Cart, CartItem
# from store.models import Product, Variation
# from .serializers import CartItemSerializer
# from django.shortcuts import get_object_or_404
# from django.core.exceptions import ObjectDoesNotExist
# from django.contrib.auth.decorators import login_required
# from django.http import HttpResponse
# from django.shortcuts import render, redirect


# class CartViewSet(ModelViewSet):
#     queryset = CartItem.objects.all()
#     serializer_class = CartItemSerializer

#     @action(detail=False, methods=['POST'])
#     def add_to_cart(self, request, product_id):
#         product = get_object_or_404(Product, id=product_id)
#         current_user = request.user
#         product_variation = []

#         for item in request.data:
#             key = item
#             value = request.data[key]

#             try:
#                 variation = Variation.objects.get(
#                     product=product, variation_category__iexact=key, variation_value__iexact=value)
#                 product_variation.append(variation)
#             except:
#                 pass

#         is_cart_item_exists = CartItem.objects.filter(
#             product=product, user=current_user).exists()

#         if is_cart_item_exists:
#             cart_item = CartItem.objects.filter(
#                 product=product, user=current_user)
#             ex_var_list = []
#             id = []
#             for item in cart_item:
#                 existing_variation = item.variations.all()
#                 ex_var_list.append(list(existing_variation))
#                 id.append(item.id)

#             if product_variation in ex_var_list:
#                 index = ex_var_list.index(product_variation)
#                 item_id = id[index]
#                 item = CartItem.objects.get(
#                     product=product, id=item_id)
#                 item.quantity += 1
#                 item.save()
#             else:
#                 item = CartItem.objects.create(
#                     product=product, quantity=1, user=current_user)
#                 if len(product_variation) > 0:
#                     item.variations.clear()
#                     item.variations.add(*product_variation)
#                 item.save()
#         else:
#             cart_item = CartItem.objects.create(
#                 product=product,
#                 quantity=1,
#                 user=current_user,
#             )
#             if len(product_variation) > 0:
#                 cart_item.variations.clear()
#                 cart_item.variations.add(*product_variation)
#             cart_item.save()

#         return Response(status=status.HTTP_201_CREATED)

#     @action(detail=False, methods=['POST'])
#     def remove_cart(self, request, product_id, cart_item_id):
#         product = get_object_or_404(Product, id=product_id)
#         current_user = request.user

#         try:
#             if current_user.is_authenticated:
#                 cart_item = CartItem.objects.get(
#                     product=product, user=current_user, id=cart_item_id)
#             else:
#                 cart = Cart.objects.get(
#                     cart_id=self._cart_id(request))
#                 cart_item = CartItem.objects.get(
#                     product=product, cart=cart, id=cart_item_id)
#             if cart_item.quantity > 1:
#                 cart_item.quantity -= 1
#                 cart_item.save()
#             else:
#                 cart_item.delete()
#         except:
#             pass

#         return Response(status=status.HTTP_204_NO_CONTENT)

#     @action(detail=False, methods=['POST'])
#     def remove_cart_item(self, request, product_id, cart_item_id):
#         product = get_object_or_404(Product, id=product_id)
#         current_user = request.user

#         if current_user.is_authenticated:
#             cart_item = CartItem.objects.get(
#                 product=product, user=current_user, id=cart_item_id)
#         else:
#             cart = Cart.objects.get(
#                 cart_id=self._cart_id(request))
#             cart_item = CartItem.objects.get(
#                 product=product, cart=cart, id=cart_item_id)

#         cart_item.delete()

#         return Response(status=status.HTTP_204_NO_CONTENT)

#     def _cart_id(self, request):
#         cart = request.session.session_key
#         if not cart:
#             cart = request.session.create()
#         return cart


# @login_required(login_url='login')
# def checkout(request, total=0, quantity=0, cart_items=None):
#     try:
#         tax = 0
#         grand_total = 0
#         if request.user.is_authenticated:
#             cart_items = CartItem.objects.filter(
#                 user=request.user, is_active=True)
#         else:
#             cart = Cart.objects.get(cart_id=_cart_id(request))
#             cart_items = CartItem.objects.filter(cart=cart, is_active=True)
#         for cart_item in cart_items:
#             total += (cart_item.product.price * cart_item.quantity)
#             quantity += cart_item.quantity
#         tax = (2 * total)/100
#         grand_total = total + tax
#     except ObjectDoesNotExist:
#         pass  # just ignore

#     context = {
#         'total': total,
#         'quantity': quantity,
#         'cart_items': cart_items,
#         'tax': tax,
#         'grand_total': grand_total,
#     }
#     return render(request, 'store/checkout.html', context)
