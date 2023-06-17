from rest_framework.generics import (
    get_object_or_404,
    ListCreateAPIView,
    ListAPIView,
    CreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveAPIView,
)
from rest_framework.views import APIView
from .models import CartItem, OrderItem, Bill, Delivery, StatusCategory, Seller
from .orderserializers import (
    CartListSerializer,
    CartSerializer,
    CartDetailSerializer,
    OrderItemSerializer,
    OrderCreateSerializer,
    OrderItemDetailSerializer,
    BillSerializer,
    BillCreateSerializer,
    BillDetailSerializer,
    StatusCategorySerializer,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .cryption import AESAlgorithm #* Bill 복호화에 사용해야함
from django.db import transaction
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

    # @transaction.atomic()
    # def create(self, request, *args, **kwargs):
    #     bill_id = self.kwargs.get("bill_id")
    #     bill = get_object_or_404(
    #         Bill, id=bill_id, user=self.request.user, is_paid=False
    #     )
    #     try:
    #         cart_ids = request.query_params.get("cart_id").split(",")
    #     except AttributeError:
    #         return Response(status=status.HTTP_400_BAD_REQUEST)

    #     cart_objects = [get_object_or_404(CartItem, id=cart_id) for cart_id in cart_ids]

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

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        try:
            bill_id = self.kwargs.get("bill_id")
            bill = get_object_or_404(
                Bill, id=bill_id, user=self.request.user, is_paid=False
            )
            cart_ids = request.query_params.get("cart_id").split(",")
        except AttributeError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        cart_objects = [get_object_or_404(CartItem, pk=cart_id) for cart_id in cart_ids]

        order_items = []
        for cart in cart_objects:
            order_item_data = {
                "product_id": cart.product.id,
                "amount": cart.amount,
                "price": cart.product.price,
                "seller": cart.product.seller,
                "bill_id": bill_id,
            }
            order_item = OrderItem(**order_item_data)
            order_items.append(order_item)
        OrderItem.objects.bulk_create(order_items)
        return Response(status=status.HTTP_201_CREATED)


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
