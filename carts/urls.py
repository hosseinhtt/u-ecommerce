from django.urls import path
from carts.views import *

app_name = 'carts'

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),
    path('add-to-cart/<int:product_id>/', AddToCartView.as_view(), name='add-to-cart'),
    path('remove-cart/<int:product_id>/<int:cart_item_id>/', RemoveCartView.as_view(), name='remove-cart'),
    path('delete-cart/<int:product_id>/<int:cart_item_id>/', RemoveCartItemView.as_view(), name='delete-cart'),

]

# Define a router for the CartItemViewSet
# from rest_framework.routers import DefaultRouter

# router = DefaultRouter()
# router.register(r'cart-items', CartItemViewSet, basename='cart-item')

# urlpatterns += router.urls
