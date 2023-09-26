from rest_framework import generics, filters, status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from store.models import Product, Variation
from category.models import Category
from carts.models import CartItem, Cart
from carts.views import CartMixin
from api.serializers import ProductSerializer, CartItemSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes

from rest_framework_simplejwt.tokens import RefreshToken # for using the login views

######################### STORE ###########################
class StoreView(generics.ListAPIView):
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['product_name', 'description']

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        queryset = Product.objects.filter(is_available=True)

        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)

        return queryset

class ProductDetailView(APIView):
    def get(self, request, category_slug, product_slug):
        try:
            product = Product.objects.get(category__slug=category_slug, slug=product_slug, is_available=True)
            cart_mixin = CartMixin()
            cart_id = cart_mixin._cart_id(request)
            in_cart = CartItem.objects.filter(cart__cart_id=cart_id, product=product).exists()

            serializer = ProductSerializer(product)
            data = serializer.data
            data['in_cart'] = in_cart
            return Response(data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

class SearchView(generics.ListAPIView):
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['product_name', 'description']

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword', '')
        queryset = Product.objects.filter(is_available=True)

        if keyword:
            queryset = queryset.filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))

        return queryset

######################### CARTS ###########################
class CartMixin:
    def _cart_id(self, request):
        cart = request.session.session_key
        if not cart:
            cart = request.session.create()
        return cart

class CartView(generics.ListAPIView):
    serializer_class = CartItemSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CartItem.objects.filter(user=user, is_active=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        total = sum(item.product.price * item.quantity for item in queryset)
        response_data = {
            'cart_items': serializer.data,
            'total': total,
        }
        return Response(response_data)


class CheckoutView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user
        if user:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            cart_items = CartItem.objects.filter(user=user, is_active=True)
            total = sum(item.product.price * item.quantity for item in cart_items)
            response_data = {
                'cart_items': CartItemSerializer(cart_items, many=True).data,
                'total': total,
                'access_token': access_token
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    

class AddToCartView(APIView, CartMixin):
    def post(self, request, product_id):
        current_user = request.user
        product = Product.objects.get(id=product_id)

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
        return Response({'detail': 'Product added to cart successfully'}, status=status.HTTP_201_CREATED)

class RemoveCartView(APIView):
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
        return Response({'detail': 'Product quantity decreased'}, status=status.HTTP_200_OK)

class RemoveCartItemView(APIView):
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
        return Response({'detail': 'Product removed from cart'}, status=status.HTTP_204_NO_CONTENT)























# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from api.serializers import RegistrationSerializer  # Import the serializer
# from accounts.models import Account, UserProfile
# from django.contrib.sites.shortcuts import get_current_site
# from django.template.loader import render_to_string
# from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
# from django.utils.encoding import force_bytes
# from django.core.mail import EmailMessage
# from django.contrib.auth.tokens import default_token_generator


# class RegisterView(APIView):
#     def post(self, request):
#         serializer = RegistrationSerializer(data=request.data)
#         if serializer.is_valid():
#             # Extract data from the serializer
#             validated_data = serializer.validated_data
#             first_name = validated_data['first_name']
#             last_name = validated_data['last_name']
#             phone_number = validated_data['phone_number']
#             email = validated_data['email']
#             password = validated_data['password']
#             username = email.split("@")[0]

#             user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
#             user.phone_number = phone_number
#             user.save()

#             # Create a user profile
#             profile = UserProfile()
#             profile.user_id = user.id
#             profile.profile_picture = 'default/default-user.png'
#             profile.save()

#             # USER ACTIVATION
#             current_site = get_current_site(request)
#             mail_subject = 'Please activate your account'
#             message = render_to_string('accounts/account_verification_email.html', {
#                 'user': user,
#                 'domain': current_site,
#                 'uid': urlsafe_base64_encode(force_bytes(user.pk)),
#                 'token': default_token_generator.make_token(user),
#             })
#             to_email = email
#             send_email = EmailMessage(mail_subject, message, to=[to_email])
#             send_email.send()
            
#             return Response({'message': 'Registration successful'}, status=status.HTTP_201_CREATED)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
