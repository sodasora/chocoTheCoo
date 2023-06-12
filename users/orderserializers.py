from rest_framework.serializers import ModelSerializer, SerializerMethodField
from users.models import CartItem, Bill, OrderItem, StatusCategory


class CartSerializer(ModelSerializer):
    class Meta:
        model = CartItem
        fields = "__all__"
        extra_kwargs = {
            "user": {"read_only": True},
        }


class CartListSerializer(ModelSerializer):
    product = SerializerMethodField()
    aggregate_price = SerializerMethodField()

    def get_aggregate_price(self, obj):
        return obj.product.price * obj.amount

    def get_product(self, obj):
        product = obj.product
        image_url = product.image.url if product.image else None
        return {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "image": image_url,
            "seller": str(product.seller),
        }

    class Meta:
        model = CartItem
        exclude = ("user",)
        depth = 1


class CartDetailSerializer(ModelSerializer):
    class Meta:
        model = CartItem
        fields = "__all__"
        extra_kwargs = {
            "user": {"read_only": True},
            "product": {"read_only": True},
        }


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"
        extra_kwargs = {
            "bill": {"read_only": True},
            "name": {"read_only": True},
            "price": {"read_only": True},
            "seller": {"read_only": True},
        }


class OrderItemDetailSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"
        depth = 1


class BillSerializer(ModelSerializer):
    order_items = SerializerMethodField()
    total_price = SerializerMethodField()

    def get_total_price(self, obj):
        order_items = obj.orderitem_set.filter(bill=obj)
        total_price = 0
        for i in order_items:
            total_price += i.price * i.amount
        return total_price

    def get_order_items(self, obj):
        order_items = obj.orderitem_set.filter(bill=obj)
        serializer = OrderItemSerializer(order_items, many=True)
        return serializer.data

    class Meta:
        model = Bill
        fields = "__all__"


class BillCreateSerializer(ModelSerializer):
    class Meta:
        model = Bill
        fields = "__all__"
        extra_kwargs = {
            "user": {"read_only": True},
            "address": {"read_only": True},
            "detail_address": {"read_only": True},
            "recipient": {"read_only": True},
            "postal_code": {"read_only": True},
        }


class BillDetailSerializer(ModelSerializer):
    order_items = SerializerMethodField()

    def get_order_items(self, obj):
        order_items = OrderItem.objects.filter(bill=obj)
        serializer = OrderItemSerializer(order_items, many=True)
        return serializer.data

    class Meta:
        model = Bill
        fields = "__all__"


class StatusCategorySerializer(ModelSerializer):
    class Meta:
        model = StatusCategory
        fields = "__all__"
