from django.urls import path, include
from api.views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'add-to-cart', AddToCartView, basename='add-to-cart')

app_name = 'api'
urlpatterns=[
    ############### Store ###########
    path('', StoreView.as_view(), name='store'),
    path('category/<slug:category_slug>/', StoreView.as_view(), name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('search/', SearchView.as_view(), name='search'),

    ############### Carts ###########
    path('cart/', CartView.as_view(), name='cart'),
    # path('add-to-cart/<int:product_id>/', AddToCartView.as_view(), name='add-to-cart'),
    path('remove-cart/<int:product_id>/<int:cart_item_id>/', RemoveCartView.as_view(), name='remove-cart'),
    path('delete-cart/<int:product_id>/<int:cart_item_id>/', RemoveCartItemView.as_view(), name='delete-cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),

    path('', include(router.urls)),




    # path('register/', RegisterView.as_view(), name='register'),

]