from rest_framework.generics import (
    get_object_or_404,
    ListCreateAPIView,
    ListAPIView,
    CreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveAPIView,
)
from rest_framework.views import APIView
from .models import CartItem, OrderItem, Bill
from .orderserializers import (
    CartListSerializer,
    CartSerializer,
    CartDetailSerializer,
    OrderItemSerializer,
    OrderItemDetailSerializer,
    BillSerializer,
    BillCreateSerializer,
    BillDetailSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

""" 
#* 작동 잘되면 제네릭API로 바꾸겠습니다 -광운- 
class CartView(ListCreateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartSerializer

class CartDetailView(RetrieveUpdateDestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartDetailSerializer

class OrderView(ListCreateAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

class OrderDetailView(RetrieveDestroyAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemDetailSerializer
"""


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """장바구니 목록 조회"""
        cart = CartItem.objects.filter(user=request.user)
        serializer = CartListSerializer(cart, many=True)
        return Response(serializer.data)

    def post(self, request):
        """장바구니 추가"""
        # 이미 존재하는 상품이면 개수 amount개 추가
        try:
            cart = CartItem.objects.get(product=request.data["product"])
            cart.amount += request.data.get("amount")
            cart.save()
            return Response({"msg": "장바구니에 추가되었습니다."}, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            if serializer.is_valid():
                serializer = CartSerializer(data=request.data)
                serializer.save()
                return Response(
                    {"msg": "장바구니에 추가되었습니다."}, status=status.HTTP_201_CREATED
                )
            return Response(
                {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )


class CartDetailView(APIView):
    """장바구니 수량 변경, 삭제"""

    permission_classes = [IsAuthenticated]

    def patch(self, request, cart_item_id):
        cart = get_object_or_404(CartItem, pk=cart_item_id)
        serializer = CartDetailSerializer(cart, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, cart_item_id):
        cart = get_object_or_404(CartItem, pk=cart_item_id)
        cart.delete()
        return Response({"msg": "장바구니 삭제"}, status=status.HTTP_204_NO_CONTENT)


class OrderListView(ListAPIView):
    """상품별 주문 목록 조회, 전체 주문 목록 조회"""

    permission_classes = [IsAuthenticated]
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        # url에서 product_id 존재하면 필터링, 없으면 전체
        if product_id:
            queryset = OrderItem.objects.filter(product_id=product_id)
        else:
            queryset = OrderItem.objects.all()
        return queryset


class OrderCreateView(CreateAPIView):
    """주문 생성"""

    permission_classes = [IsAuthenticated]
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def perform_create(self, serializer):
        bill_id = self.kwargs.get("bill_id")
        bill = get_object_or_404(Bill, pk=bill_id)
        serializer.save(bill=bill)


class OrderDetailView(RetrieveUpdateAPIView):
    """주문 상세 조회"""

    permission_classes = [IsAuthenticated]
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemDetailSerializer


class BillView(ListCreateAPIView):
    """주문 내역 조회"""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return BillSerializer
        elif self.request.method == "POST":
            return BillCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = Bill.objects.filter(user=self.request.user)
        return queryset


class BillDetailView(RetrieveAPIView):
    """주문 내역 상세 조회"""

    permission_classes = [IsAuthenticated]
    serializer_class = BillDetailSerializer

    def get_queryset(self):
        queryset = Bill.objects.filter(user=self.request.user)
        return queryset

    def get_object(self):
        pk = self.kwargs.get("pk")
        obj = self.get_queryset().get(pk=pk)
        return obj