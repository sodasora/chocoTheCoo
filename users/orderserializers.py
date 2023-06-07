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
    product = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        exclude = ('user',)
        depth = 1

    def get_product(self, cart_item):
        product = cart_item.product
        image_url = product.image.url if product.image else None
        return {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'image': image_url,
            'seller': product.seller.company_name,
        }

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
