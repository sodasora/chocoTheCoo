from rest_framework import serializers
from users.models import CartItem, OrderItem, Bill

class CartSerializer(serializers.ModelSerializer):
    # price = serializers.SerializerMethodField()
    # total_price = serializers.SerializerMethodField()
    # image = serializers.SerializerMethodField()

    # def get_image(self, obj):
    #     return obj.product.image

    # def get_total_price(self, obj):
    #     return obj.product.price * obj.count

    # def get_price(self, obj):
    #     return obj.product.price

    class Meta:
        model = CartItem
        fields = '__all__'

class CartListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'
        depth = 1

class CartDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'
        
class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = '__all__'
