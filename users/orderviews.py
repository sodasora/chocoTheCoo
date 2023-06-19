from math import ceil
from django.core.exceptions import PermissionDenied
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
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CartItem, OrderItem, Bill, Delivery, Point, StatusCategory, Seller
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
    StatusCategorySerializer,
)
from .cryption import AESAlgorithm  # * Bill 복호화에 사용해야함
from config.permissions_ import IsDeliveryRegistered


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """장바구니 목록 조회"""

        try:  # url 쿼리 파라미터로 id가 전달되면 해당 값들만 조회
            cart_ids = request.query_params.get("cart_id").split(",")
            if cart_ids:
                cart_items = CartItem.objects.filter(user=request.user, id__in=cart_ids)
                serializer = CartListSerializer(cart_items, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except AttributeError:  # 쿼리 파라미터가 없으면 .split에서 에러 / 전체 조회
            cart = CartItem.objects.filter(user=request.user)
            serializer = CartListSerializer(cart, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """장바구니 추가"""

        try:  # 이미 존재하는 상품이면 개수 amount개 추가
            cart = CartItem.objects.get(
                product=request.data["product"], user=request.user
            )
            cart.amount += request.data.get("amount")
            cart.save()
            return Response({"msg": "장바구니에 추가되었습니다."}, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            serializer = CartSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(
                    {"msg": "장바구니에 추가되었습니다."}, status=status.HTTP_201_CREATED
                )
            return Response(
                {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request):
        try:
            cart_ids = request.query_params.get("cart_id").split(",")
            cart_items = CartItem.objects.filter(user=request.user, id__in=cart_ids)
            if cart_items:
                for cart in cart_items:
                    cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except AttributeError:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class CartDetailView(APIView):
    """장바구니 수량 변경"""

    permission_classes = [IsAuthenticated]

    def patch(self, request, cart_item_id):
        cart = get_object_or_404(CartItem, pk=cart_item_id, user=request.user)
        serializer = CartDetailSerializer(cart, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class OrderListView(ListAPIView):
    """상품별 주문 목록 조회, 판매자별 주문 목록 조회, 전체 주문 목록 조회"""

    permission_classes = [IsAuthenticated]
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        user_id = self.kwargs.get("user_id")
        # url에서 product_id 존재하면 필터링, 없으면 전체
        if product_id:
            queryset = OrderItem.objects.filter(product_id=product_id)
        elif user_id:
            seller = Seller.objects.get(user=user_id)
            queryset = OrderItem.objects.filter(seller=seller.id)
        else:
            queryset = OrderItem.objects.all()
        return queryset


class OrderCreateView(CreateAPIView):
    """주문 생성"""

    permission_classes = [IsAuthenticated | IsDeliveryRegistered]
    queryset = OrderItem.objects.all()
    serializer_class = OrderCreateSerializer

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        # bill이 생성되었는지 확인, 생성되지 않았다면 400
        bill_id = self.kwargs.get("bill_id")
        bill = get_object_or_404(
            Bill, id=bill_id, user=self.request.user, is_paid=False
        )

        # cart_ids 리스트 => 해당하는 객체 쿼리셋 조회
        try:
            cart_ids = request.query_params.get("cart_id").split(",")
            cart_objects = CartItem.objects.filter(pk__in=cart_ids)
            total_buy_price = sum(
                [(cart.product.price * cart.amount) for cart in cart_objects]
            )
        except AttributeError:  # url params 오류
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 유저 포인트 차감 및 적립하기
        try:
            OrderPointCreate(request.user, total_buy_price)
        except PermissionDenied:  # 포인트 부족
            bill.delete()
            return Response(status=status.HTTP_403_FORBIDDEN)

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
                order_item = OrderItem(**order_item_data)
                order_items.append(order_item)
            # bulk_create로 장바구니 => 주문상품으로 옮겨줌. 성공시 201
            OrderItem.objects.bulk_create(order_items)
            return Response(status=status.HTTP_201_CREATED)

        # NotNull Constraints Failed.
        # cart또는 product가 정상적인 상태로 저장되지 않았음.
        except IntegrityError:
            bill.delete()
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # statusCategory가 생성되지 않았음.
        except StatusCategory.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    #     order_items = []
    #     for cart in cart_objects:
    #         order_item_data = {
    #             "product_id": cart.product.id,
    #             "amount": cart.amount,
    #             "price": cart.product.price,
    #             "name": cart.product.name,
    #             "seller": cart.product.seller.id,
    #         }
    #         order_items.append(order_item_data)

    #     serializer = self.get_serializer(data=order_items, many=True)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save(bill=bill)
    #     return Response(status=status.HTTP_201_CREATED)


def OrderPointCreate(user: object, total_buy_price: int):
    """주문 상품 포인트 생성"""
    total_plus_point = (
        Point.objects.filter(user_id=user.id)
        .filter(point_type__in=[1, 2, 3, 4, 5])
        .aggregate(total=Sum("point"))
    ).get("total", 0) or 0
    total_minus_point = (
        Point.objects.filter(user_id=user.id)
        .filter(point_type__in=[6, 7])
        .aggregate(total=Sum("point"))
    ).get("total", 0) or 0

    if total_plus_point < (total_buy_price + total_minus_point):
        raise PermissionDenied("결제를 위한 포인트가 부족합니다")

    buy_point_earn = ceil(total_buy_price / 20)

    Point.objects.create(user=user, point_type_id=7, point=total_buy_price)
    Point.objects.create(user=user, point_type_id=4, point=buy_point_earn)


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
            self.permission_classes = [IsAuthenticated | IsDeliveryRegistered]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return BillSerializer
        elif self.request.method == "POST":
            return BillCreateSerializer

    def perform_create(self, serializer):
        deli = get_object_or_404(Delivery, pk=self.request.data.get("delivery_id"))
        serializer.save(
            user=self.request.user,
            address=deli.address,
            detail_address=deli.detail_address,
            recipient=deli.recipient,
            postal_code=deli.postal_code,
        )

    def get_queryset(self):
        queryset = Bill.objects.filter(user=self.request.user)
        return queryset


class BillDetailView(RetrieveAPIView):
    """주문 내역 상세 조회"""

    permission_classes = [IsAuthenticated | IsDeliveryRegistered]
    serializer_class = BillDetailSerializer

    def get_queryset(self):
        queryset = Bill.objects.filter(user=self.request.user)
        return queryset


class StatusCategoryView(ListCreateAPIView):
    """주문 상태 생성, 목록 조회"""

    permission_classes = [IsAdminUser]
    serializer_class = StatusCategorySerializer
    queryset = StatusCategory.objects.all()
