from django.urls import path
from store.views import *

app_name = 'store'

urlpatterns = [
    path('', StoreView.as_view(), name='store'),
    path('<slug:category_slug>/', StoreView.as_view(), name='products_by_category'),
    path('<slug:category_slug>/<slug:product_slug>', ProductDetailView.as_view(), name='product_detail'),
]