from rest_framework import generics
from rest_framework.views import APIView
from .models import CartItem, Seller
from products.models import Product
from .orderserializers import *
from rest_framework.response import Response
from rest_framework import status

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
    def get(self, request):
        """ 장바구니 목록 조회 """
        cart = CartItem.objects.filter(user=request.user)
        serializer = CartListSerializer(cart, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """ 장바구니 추가 """
        cart = CartItem.objects.filter(product=request.data['product'])
        # 이미 존재하는 상품이면 개수 amount개 추가
        if cart:
            cart[0].amount += request.data.get('amount')
            cart[0].save()
            return Response({'msg': "장바구니에 추가되었습니다."}, status=status.HTTP_200_OK)
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': "장바구니에 추가되었습니다."}, status=status.HTTP_201_CREATED)
        return Response({"err":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class CartDetailView(APIView):
    """ 장바구니 수량 변경, 삭제 """
    #? 장바구니 상세 조회 > 목록으로 충분 / 상품 누르면 상품페이지로 이동하게.
    def patch(self, request, cart_item_id):
        cart = generics.get_object_or_404(CartItem, pk=cart_item_id)
        serializer = CartDetailSerializer(cart, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"err":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, cart_item_id):
        cart = generics.get_object_or_404(CartItem, pk=cart_item_id)
        cart.delete()
        return Response({'msg': "장바구니 삭제"}, status=status.HTTP_204_NO_CONTENT)
    
class OrderListView(generics.ListAPIView):
    """ 상품별 주문 목록 조회 """
    serializer_class = OrderItemSerializer
    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        queryset = OrderItem.objects.filter(product_id=product_id)
        return queryset

class OrderCreateView(generics.CreateAPIView):
    """ 주문 생성 """
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    def perform_create(self, serializer):
        bill_id = self.kwargs.get('bill_id')
        bill = generics.get_object_or_404(Bill, pk=bill_id)
        serializer.save(bill=bill)

class OrderDetailView(generics.RetrieveUpdateAPIView):
    """ 주문 상세 조회 """
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemDetailSerializer

class BillView(generics.ListCreateAPIView):
    """ 주문 내역 조회 """
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return BillSerializer
        elif self.request.method == 'POST':
            return BillCreateSerializer
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = Bill.objects.filter(user=self.request.user)
        return queryset

class BillDetailView(generics.RetrieveAPIView):
    """ 주문 내역 상세 조회 """
    queryset = Bill.objects.all()
    serializer_class = BillDetailSerializer
    def get_object(self):
        pk = self.kwargs.get('pk')
        obj = self.get_queryset().get(pk=pk, user_id=self.request.user.id)
        return obj
    
        # ! 해당 obj가 없을 때, get에서 자체적으로 에러를 발생, 예외처리 어떻게 해야할지 방법 찾아야함.
        # try:
        # except Bill.DoesNotExist:
        #     raise Response({'msg': "해당 주문내역이 없습니다."}, status=status.HTTP_404_NOT_FOUND)
