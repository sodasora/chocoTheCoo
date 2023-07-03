from math import ceil
from django.core.exceptions import PermissionDenied
from rest_framework.serializers import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.db.utils import IntegrityError
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    get_object_or_404,
    ListCreateAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from products.models import Product
from users.serializers import DeliverySerializer
from users.validated import ValidatedData
from .models import (
    CartItem,
    OrderItem,
    Bill,
    Delivery,
    Point,
    StatusCategory,
    Seller,
    PhoneVerification,
)
from .orderserializers import (
    BillCreateSerializer,
    BillDetailSerializer,
    BillSerializer,
    CartDetailSerializer,
    CartListSerializer,
    CartSerializer,
    OrderCreateSerializer,
    OrderItemDetailSerializer,
    OrderItemSerializer,
    OrderStatusSerializer,
    StatusCategorySerializer,
)
from config.permissions_ import IsDeliveryRegistered


class CartView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = CartItem.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CartSerializer
        else:
            return CartListSerializer

    def get_queryset(self):
        queryset = CartItem.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )
        try:  # url 쿼리 파라미터로 id가 전달되면 해당 값들만 조회
            if self.request.user.phone_verification.is_verified is not True:
                raise ValidationError("핸드폰 인증이 필요합니다.")
            cart_id = self.request.query_params.get("cart_id").split(",")
            queryset = queryset.filter(id__in=cart_id)
            return queryset
        except PhoneVerification.DoesNotExist:
            raise ValidationError("핸드폰 정보가 없습니다.")
        except AttributeError:  # 쿼리 파라미터가 없으면 .split에서 에러 / 전체 조회
            return queryset

    def post(self, request, *args, **kwargs):
        """장바구니 추가"""

        # 상품 아이디로 추가
        if product_id := request.data.get("product"):
            product = get_object_or_404(Product, id=product_id, item_state=1)
            amount = int(request.data.get("amount"))
            self.add_exist_cart(product, amount)

        # 주문내역 아이디로 추가
        elif bill_id := request.data.get("bill_id"):
            bill = get_object_or_404(Bill, pk=bill_id)
            order_items = bill.orderitem_set.all()
            for orderitem in order_items:
                product = get_object_or_404(
                    Product, pk=orderitem.product_id, item_state=1
                )
                amount = orderitem.amount
                self.add_exist_cart(product, amount)

        # 주문상품 아이디로 추가
        elif order_item_id := request.data.get("order_item_id"):
            orderitem = get_object_or_404(OrderItem, id=order_item_id)
            product = get_object_or_404(Product, pk=orderitem.product_id, item_state=1)
            amount = orderitem.amount
            self.add_exist_cart(product, amount)
        return Response({"msg": "장바구니에 추가되었습니다."}, status=status.HTTP_200_OK)

    # 이미 존재하는 상품이면 개수 amount개 추가
    def add_exist_cart(self, product, amount):
        cart_item, created = CartItem.objects.get_or_create(
            product=product, user=self.request.user, defaults={"amount": amount}
        )
        if not created:
            cart_item.amount += amount
            cart_item.save()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        cart_items = self.get_queryset()
        if cart_items.exists():
            cart_items.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class CartDetailView(UpdateAPIView):
    """장바구니 수량 변경"""

    permission_classes = [IsAuthenticated]
    serializer_class = CartDetailSerializer

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)


class OrderListView(ListAPIView):
    """상품별 주문 목록 조회, 판매자별 주문 목록 조회, 전체 주문 목록 조회"""

    permission_classes = [IsAuthenticated]
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        # url에서 product_id 존재하면 필터링, 없으면 해당 판매자 주문 조회
        if product_id := self.kwargs.get("product_id"):
            queryset = OrderItem.objects.filter(product_id=product_id)
        else:
            queryset = OrderItem.objects.filter(seller=self.request.user.pk)
        return queryset


class OrderCreateView(CreateAPIView):
    """주문 생성"""

    permission_classes = [IsAuthenticated, IsDeliveryRegistered]
    queryset = OrderItem.objects.all()
    serializer_class = OrderCreateSerializer

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        # bill이 생성되었는지 확인, 생성되지 않았다면 404
        bill_id = self.kwargs.get("bill_id")
        bill = get_object_or_404(
            Bill, id=bill_id, user=self.request.user, is_paid=False
        )

        # cart_ids 리스트 => 해당하는 객체 쿼리셋 조회
        try:
            cart_ids: list = request.query_params.get("cart_id").split(",")
            cart_objects = CartItem.objects.filter(pk__in=cart_ids)
            total_buy_price = sum(
                [(cart.product.price * cart.amount) for cart in cart_objects]
            )
        except AttributeError:  # url params 오류
            bill.delete()
            return Response(
                {"err": "no_cart"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 유저 포인트 차감 및 적립하기
        try:
            order_point_create(request.user, total_buy_price)
        except PermissionDenied as e:  # 포인트 부족
            bill.delete()
            return Response({"err": str(e)}, status=status.HTTP_403_FORBIDDEN)

        # orderitem 객체 리스트 생성
        try:
            is_paid = StatusCategory.objects.get(pk=2)
            order_items = []
            for cart in cart_objects:
                order_item_data = {
                    "name": cart.product.name,
                    "product_id": cart.product.id,
                    "amount": cart.amount,
                    "price": cart.product.price,
                    "seller": cart.product.seller,
                    "bill_id": bill_id,
                    "order_status": is_paid,
                }
                if cart.product.image:
                    order_item_data["image"] = cart.product.image.url
                order_item = OrderItem(**order_item_data)
                order_items.append(order_item)
                product_amount_deduction(product=cart.product, buy_amount=cart.amount)

            # bulk_create로 장바구니 => 주문상품으로 옮겨줌. 성공시 201
            OrderItem.objects.bulk_create(order_items)
            bill.is_paid = True
            bill.save()
            return Response({"msg": "생성 완료"}, status=status.HTTP_201_CREATED)

        # 상품 재고량 부족
        except ValidationError as e:
            bill.delete()
            return Response(
                {"err": e.detail[0].code}, status=status.HTTP_400_BAD_REQUEST
            )
        # NotNull Constraints Failed.
        # cart또는 product가 정상적인 상태로 저장되지 않았음.,.
        except IntegrityError:
            bill.delete()
            return Response(
                {"err": "incorrect_product"}, status=status.HTTP_400_BAD_REQUEST
            )
        # statusCategory가 생성되지 않았음.
        except StatusCategory.DoesNotExist:
            bill.delete()
            return Response(
                {"err": "status_not_exist"}, status=status.HTTP_404_NOT_FOUND
            )

    #     order_items.append(order_item_data)
    #     serializer = self.get_serializer(data=order_items, many=True)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save(bill=bill)


def order_point_create(user: object, total_buy_price: int):
    """주문 상품 포인트 생성"""
    total_plus_point = (
        Point.objects.filter(user_id=user.id)
        .filter(point_type__in=[1, 2, 3, 4, 5, 8])
        .aggregate(total=Sum("point"))
    ).get("total", 0) or 0
    total_minus_point = (
        Point.objects.filter(user_id=user.id)
        .filter(point_type__in=[6, 7])
        .aggregate(total=Sum("point"))
    ).get("total", 0) or 0

    if total_plus_point < (total_buy_price + total_minus_point):
        raise PermissionDenied("insufficient_balance")

    try:
        is_subscribed = int(user.subscribe_data.subscribe)
    except:
        is_subscribed = 0

    buy_point_earn = ceil(total_buy_price / 20) * (1 + is_subscribed)

    Point.objects.create(user=user, point_type_id=7, point=total_buy_price)
    Point.objects.create(user=user, point_type_id=4, point=buy_point_earn)


def product_amount_deduction(product: object, buy_amount: int):
    """주문 시 상품 재고량 감소"""
    if product.amount < buy_amount:
        raise ValidationError(code="out_of_stock")
    else:
        product.amount -= buy_amount
        if product.amount == 0:
            product.item_state = 2
        product.save()


class OrderDetailView(RetrieveUpdateAPIView):
    """주문 상세 조회"""

    permission_classes = [IsAuthenticated]
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemDetailSerializer


class BillView(ListCreateAPIView):
    """주문 내역 조회"""

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated, IsDeliveryRegistered]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return BillSerializer
        elif self.request.method == "POST":
            return BillCreateSerializer

    def create(self, request, *args, **kwargs):
        # 기존 배송정보 사용 시
        if delivery_id := self.request.data.get("delivery_id"):
            deli = get_object_or_404(Delivery, pk=delivery_id)
            data = {
                "user": request.user,
                "address": deli.address,
                "detail_address": deli.detail_address,
                "recipient": deli.recipient,
                "postal_code": deli.postal_code,
            }
            serializer = self.get_serializer(
                data=data, context={"skip_validation": True}
            )
        # 새로운 배송정보 입력 시
        elif request.data.get("postal_code") and request.data.get("recipient"):
            data = request.data
            serializer = self.get_serializer(data=data, context={"user": request.user})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = Bill.objects.filter(user=self.request.user).order_by("-created_at")
        return queryset


class BillDetailView(RetrieveAPIView):
    """주문 내역 상세 조회"""

    permission_classes = [IsAuthenticated, IsDeliveryRegistered]
    serializer_class = BillDetailSerializer

    def get_queryset(self):
        queryset = Bill.objects.filter(user=self.request.user)
        return queryset


class StatusCategoryView(ListAPIView):
    """주문 상태 목록 조회"""

    serializer_class = StatusCategorySerializer
    queryset = StatusCategory.objects.all()


class StatusChangeView(UpdateAPIView):
    """주문 상태 변경"""

    permission_classes = [IsAuthenticated]
    serializer_class = OrderStatusSerializer
    queryset = OrderItem.objects.all()

    def perform_update(self, serializer):
        order_item = self.get_object()
        cur_status = order_item.order_status.id
        new_status = self.request.data.get("order_status")
        if cur_status == 5 and new_status == 6:
            seller = order_item.seller.user
            total_point = order_item.amount * order_item.price
            Point.objects.create(user=seller, point_type_id=8, point=total_point)
        serializer.save()
