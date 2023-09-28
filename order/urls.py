from django.urls import path
from order.views import *

app_name='order'

urlpatterns = [
    path('payments/', PaymentsView.as_view(), name='payments'),
    path('place-order/', PlaceOrderView.as_view(), name='place-order'),
    path('order-complete/', OrderCompleteView.as_view(), name='order-complete'),
]