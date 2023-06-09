from rest_framework import serializers
from users.models import CartItem, Bill, OrderItem,StatusCategory

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'

class CartListSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        exclude = ('user',)
        depth = 1

    def get_product(self, obj):
        product = obj.product
        image_url = product.image.url if product.image else None
        return {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'total_price': product.price * obj.amount,
            'image': image_url,
            'seller': str(product.seller),
        }

class CartDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True},
            'product': {'read_only': True},
        }

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'
        extra_kwargs = { 
            'bill': {'read_only': True},
        }

class OrderItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'
        depth = 1

class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = '__all__'

class BillCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True},
        }

class BillDetailSerializer(serializers.ModelSerializer):
    order_items = serializers.SerializerMethodField()

    def get_order_items(self, obj):
        order_items = OrderItem.objects.filter(bill=obj)
        serializer = OrderItemSerializer(order_items, many=True)
        return serializer.data

    class Meta:
        model = Bill
        fields = '__all__'


class StatusCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusCategory
        fields = '__all__'