from rest_framework import serializers
from users.models import CartItem, OrderItem, Bill

class CartListCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'

class CartUpdateDestroySerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'
