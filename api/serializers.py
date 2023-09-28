# serializers.py
from rest_framework import serializers
from store.models import Product, Variation
from carts.models import CartItem
from order.models import Payment, Order, OrderProduct


class VariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variation
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    variations = VariationSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'



class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    order_products = OrderProductSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'





# from rest_framework import serializers

# class RegistrationSerializer(serializers.Serializer):
#     first_name = serializers.CharField(max_length=30)
#     last_name = serializers.CharField(max_length=30)
#     phone_number = serializers.CharField(max_length=15)
#     email = serializers.EmailField()
#     password = serializers.CharField(max_length=128)
