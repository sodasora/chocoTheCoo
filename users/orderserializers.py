from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
)
from users.models import CartItem, Bill, OrderItem, StatusCategory
from products.models import Product
from .cryption import AESAlgorithm


class CartSerializer(ModelSerializer):
    """
    장바구니 생성 시리얼라이저
    """

    class Meta:
        model = CartItem
        fields = "__all__"
        extra_kwargs = {
            "user": {"read_only": True},
        }


class CartListSerializer(ModelSerializer):
    """
    장바구니 목록 조회 시리얼라이저
    """

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
    """
    장바구니 수량 변경, 삭제 시리얼라이저
    """

    class Meta:
        model = CartItem
        fields = "__all__"
        read_only_fields = ("user", "product")


class OrderCreateSerializer(ModelSerializer):
    """
    주문 목록 생성 시리얼라이저
    """

    class Meta:
        model = OrderItem
        fields = ("product_id", "amount", "price", "seller")


class OrderItemSerializer(ModelSerializer):
    """
    주문 생성, 목록 조회 시리얼라이저
    """

    product_image = SerializerMethodField()

    def get_product_image(self, obj):
        product = Product.objects.get(pk=obj.product_id)
        return product.image.url if product.image else None

    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ("bill", "name", "price", "seller")
        depth = 1


class OrderItemBillSerializer(OrderItemSerializer):
    order_status = SerializerMethodField()

    def get_order_status(self, obj):
        return obj.order_status.name

    class Meta:
        model = OrderItem
        exclude = ("bill",)


class OrderItemDetailSerializer(ModelSerializer):
    """
    주문 상품 상세 조회 시리얼라이저
    """

    class Meta:
        model = OrderItem
        fields = "__all__"
        depth = 1


class BillSerializer(ModelSerializer):
    """
    주문서 목록 조회 시리얼라이저
    """

    order_items_count = SerializerMethodField()
    total_price = SerializerMethodField()
    thumbnail = SerializerMethodField()
    thumbnail_name = SerializerMethodField()
    bill_order_status = SerializerMethodField()

    def get_bill_order_status(self, obj):
        if obj.is_paid == False:
            return "결제대기"
        else:
            temp = {i.order_status.id for i in obj.orderitem_set.all()}
            return StatusCategory.objects.get(id=min(temp)).name if temp else 1

    def get_thumbnail_name(self, obj):
        try:
            ord_item = obj.orderitem_set.all()[0]
            product = Product.objects.get(pk=ord_item.product_id)
        except:
            return None
        return product.name

    def get_thumbnail(self, obj):
        thumbnail = []
        ord_list = obj.orderitem_set.all()
        for i in ord_list:
            try:
                product = Product.object.get(pk=i.product_id)
                thumbnail.append(product.image)
            except:
                pass
        return thumbnail

    def get_total_price(self, obj):
        order_items = obj.orderitem_set.filter(bill=obj)
        total_price = 0
        for i in order_items:
            total_price += i.price * i.amount
        return total_price

    def get_order_items_count(self, obj):
        return obj.orderitem_set.all().count()

    def to_representation(self, instance):
        """
        배송지 모델  데이터 복호화
        """
        information = super().to_representation(instance)
        decrypt_result = AESAlgorithm.decrypt_all(**information)
        return decrypt_result

    class Meta:
        model = Bill
        fields = "__all__"


class BillCreateSerializer(ModelSerializer):
    """
    주문서 생성 시리얼라이저
    """

    class Meta:
        model = Bill
        fields = "__all__"
        read_only_fields = (
            "user",
            "address",
            "detail_address",
            "recipient",
            "postal_code",
        )


class BillDetailSerializer(ModelSerializer):
    """
    주문서 상세 조회 시리얼라이저
    """

    bill_order_status = SerializerMethodField()
    order_items = SerializerMethodField()
    total_price = SerializerMethodField()

    def get_bill_order_status(self, obj):
        if obj.is_paid == False:
            return "결제대기"
        else:
            temp = {i.order_status.id for i in obj.orderitem_set.all()}
            return StatusCategory.objects.get(id=min(temp)).name if temp else 1

    def get_order_items(self, obj):
        order_items = obj.orderitem_set.all()
        serializer = OrderItemBillSerializer(order_items, many=True)
        return serializer.data

    def get_total_price(self, obj):
        order_items = obj.orderitem_set.filter(bill=obj)
        total_price = 0
        for i in order_items:
            total_price += i.price * i.amount
        return total_price

    def to_representation(self, instance):
        """
        배송지 모델  데이터 복호화
        """
        information = super().to_representation(instance)
        decrypt_result = AESAlgorithm.decrypt_all(**information)
        return decrypt_result

    class Meta:
        model = Bill
        fields = "__all__"


class StatusCategorySerializer(ModelSerializer):
    """
    주문 상태 카테고리 생성, 조회 시리얼라이저
    """

    class Meta:
        model = StatusCategory
        fields = "__all__"
