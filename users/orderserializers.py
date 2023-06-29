from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    StringRelatedField,
)
from users.models import CartItem, Bill, OrderItem, StatusCategory
from products.models import Product
from users.validated import ValidatedData
from .cryption import AESAlgorithm
from products.serializers import SimpleSellerInformation
from rest_framework.serializers import ValidationError, PrimaryKeyRelatedField


class StatusCategorySerializer(ModelSerializer):
    """
    주문 상태 카테고리 생성, 조회 시리얼라이저
    """

    class Meta:
        model = StatusCategory
        fields = "__all__"


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


class OrderItemDetailSerializer(ModelSerializer):
    """
    주문 상품 상세 조회 시리얼라이저
    """

    class Meta:
        model = OrderItem
        fields = "__all__"
        depth = 1


class SimpleBillSerializer(ModelSerializer):
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


class BillSerializer(ModelSerializer):
    """
    주문서 목록 조회 시리얼라이저
    """

    order_items_count = SerializerMethodField()
    total_price = SerializerMethodField()
    thumbnail = SerializerMethodField()
    bill_order_status = SerializerMethodField()

    def get_bill_order_status(self, obj):
        if obj.is_paid == False:
            return "결제대기"
        else:
            temp = {i.order_status.id for i in obj.orderitem_set.all()}
            return StatusCategory.objects.get(id=min(temp)).name if temp else 1

    def get_thumbnail(self, obj):
        ord_list = obj.orderitem_set.all()
        for order_item in ord_list:
            if order_item.image:
                return {"image": order_item.image, "name": order_item.name}
        return {"image": None, "name": ord_list.first().name}

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
        read_only_fields = ("user",)

    def validate(self, deliveries_data):
        """
        우편 번호 검증
        """
        # 기존 배송정보 사용 시 밸리데이션 PASS

        if self.context.get("skip_validation") is True:
            return deliveries_data
        user = self.context.get("user")
        verification_result = ValidatedData.validated_deliveries(user, deliveries_data)
        if verification_result is not True:
            raise ValidationError(verification_result[1])
        return deliveries_data

    def encrypt_deliveries_information(self, deliveries, validated_data):
        """
        오브 젝트 암호화
        """
        # 기존 배송정보 사용 시 암호화 PASS
        if self.context.get("skip_validation") is True:
            return deliveries
        encrypt_result = AESAlgorithm.encrypt_all(**validated_data)
        deliveries.address = encrypt_result.get("address")
        deliveries.detail_address = encrypt_result.get("detail_address")
        deliveries.recipient = encrypt_result.get("recipient")
        deliveries.postal_code = encrypt_result.get("postal_code")
        deliveries.save()
        return deliveries

    def create(self, validated_data):
        """ "
        배송 정보 오브 젝트 생성
        """
        deliveries = super().create(validated_data)
        deliveries = self.encrypt_deliveries_information(deliveries, validated_data)
        deliveries.save()
        return deliveries


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
            return StatusCategory.objects.get(id=min(temp)).name if temp else "결제대기"

    def get_order_items(self, obj):
        order_items = obj.orderitem_set.all()
        serializer = SimpleOrderItemSerializer(order_items, many=True)
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
        # print(decrypt_result)
        return decrypt_result

    class Meta:
        model = Bill
        fields = "__all__"


class OrderItemSerializer(ModelSerializer):
    """
    주문 목록 조회 시리얼라이저
    """

    bill = SimpleBillSerializer()
    seller = SimpleSellerInformation()
    order_status = StatusCategorySerializer()

    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ("bill", "name", "price", "seller")


class SimpleOrderItemSerializer(ModelSerializer):
    order_status = StringRelatedField()

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderStatusSerializer(ModelSerializer):
    order_status = PrimaryKeyRelatedField(
        queryset=StatusCategory.objects.all(), required=True
    )

    class Meta:
        model = OrderItem
        fields = ("order_status",)

    def validate_order_status(self, value):
        request = self.context["request"]
        user = request.user
        cur_status = self.instance.order_status.id
        seller = self.instance.seller == user.user_seller
        buyer = self.instance.bill.user == user

        if cur_status in [2, 3, 4] and value.id in [2, 3, 4, 5]:
            if not seller:
                raise ValidationError("주문 상품의 판매자만 변경 가능합니다")
        elif cur_status == 5 and value.id == 6:
            if not buyer:
                raise ValidationError("상품의 구매자만 변경 가능합니다")
        elif cur_status in [1, 6]:
            raise ValidationError("현재 상태에서 주문 상태를 수정할 수 없습니다.")
        else:
            raise ValidationError("유효하지 않은 주문 상태입니다.")
        return value
