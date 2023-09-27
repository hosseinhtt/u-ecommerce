from django.shortcuts import get_object_or_404
from django.db.models import Q
from store.models import Product, Variation
from category.models import Category
from carts.models import CartItem, Cart
from carts.views import CartMixin
from api.serializers import ProductSerializer, CartItemSerializer
from api.forms import AddToCartForm
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from rest_framework import viewsets, status, generics, filters
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
            tax = 2*total/100
            final = tax+total
            serializer = CartItemSerializer(cart_items, many=True)

            response_data = {
                'cart_items': serializer.data,
                'total': total,
                'tax': tax,
                'total_price': final,
                'access_token': access_token
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class AddToCartView(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    queryset = CartItem.objects.all()

    def create(self, request, *args, **kwargs):
        # Retrieve the product based on the product_id
        product = get_object_or_404(Product, id=kwargs.get('product_id'))

        # Get the JSON data from the request body
        data = request.data

        # Assuming the JSON data includes 'variations' as a list of variation IDs
        variation_ids = data.get('variations', [])

        # Create or get the user's cart based on their authentication status
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            cart_id = request.session.get('cart_id')
            if cart_id:
                cart = get_object_or_404(Cart, id=cart_id)
            else:
                cart = Cart.objects.create()

        # Create or update the cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            user=request.user if request.user.is_authenticated else None,
        )

        # Add the selected variations to the cart item
        if variation_ids:
            variations = Variation.objects.filter(id__in=variation_ids)
            cart_item.variations.set(variations)

        # Update the quantity based on the request data
        quantity = data.get('quantity', 1)
        cart_item.quantity = quantity
        cart_item.save()

        # Serialize the cart item for response
        cart_item_serializer = CartItemSerializer(cart_item)

        return Response({'detail': 'Product added to cart successfully', 'cart_item': cart_item_serializer.data}, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        # Retrieve the cart item based on the item_id
        item_id = kwargs.get('pk')
        cart_item = get_object_or_404(CartItem, id=item_id)

        # Update the quantity based on the request data
        quantity = request.data.get('quantity')
        if quantity is not None:
            cart_item.quantity = quantity
            cart_item.save()

        # Serialize the updated cart item for response
        cart_item_serializer = CartItemSerializer(cart_item)

        return Response({'detail': 'Cart item updated successfully', 'cart_item': cart_item_serializer.data})

    def destroy(self, request, *args, **kwargs):
        # Retrieve the cart item based on the item_id
        item_id = kwargs.get('pk')
        cart_item = get_object_or_404(CartItem, id=item_id)

        # Delete the cart item
        cart_item.delete()

        return Response({'detail': 'Cart item deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
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
        except ObjectDoesNotExist:
            pass

        return Response({'detail': 'Product quantity decreased'}, status=status.HTTP_200_OK)

class RemoveCartItemView(APIView):
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

            cart_item.delete()
        except ObjectDoesNotExist:
            pass

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
