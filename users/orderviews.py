from rest_framework.generics import get_object_or_404, ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveDestroyAPIView, RetrieveAPIView
from rest_framework.views import APIView
from .models import CartItem
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
    # def get(self, request, pk):
    """ 
    #? 장바구니 상세 조회 > 목록으로 충분 / 상품 누르면 상품페이지로 이동하게.
    """
    #     cart = get_object_or_404(CartItem, pk=pk)
    #     serializer = CartDetailSerializer(cart)
    #     return Response(serializer.data)

    def patch(self, request, cart_item_id):
        cart = get_object_or_404(CartItem, pk=cart_item_id)
        serializer = CartDetailSerializer(cart, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"err":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, cart_item_id):
        cart = get_object_or_404(CartItem, pk=cart_item_id)
        cart.delete()
        return Response({'msg': "장바구니 삭제"}, status=status.HTTP_204_NO_CONTENT)
    
# class OrderView(ListCreateAPIView):
#     def get(self, request, bill_id=None, seller_id=None):
#         bill = get_object_or_404(Bill, user=request.user)
#         if bill_id:
#             order = OrderItem.objects.filter(bill=bill)
#             serializer = OrderItemSerializer(order, many=True)
#             return Response(serializer.data)
#         else:
#             order = OrderItem.objects.filter(seller=seller_id)
#             serializer = OrderItemSerializer(order, many=True)
#             return Response(serializer.data)

#     def post(self, request, bill_id):
#         bill = get_object_or_404(Bill, pk=bill_id)
#         serializer = OrderItemSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(bill=bill)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response({"err":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# class OrderDetailView(APIView):
#     def get(self, request, pk):
#         order = get_object_or_404(OrderItem, pk=pk)
#         serializer = OrderItemDetailSerializer(order)
#         return Response(serializer.data)

#     def put(self, request, pk):
#         order = get_object_or_404(OrderItem, pk=pk)
#         serializer = OrderItemDetailSerializer(order, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({'msg': ""}, status=status.HTTP_200_OK)
#         return Response({"err":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk):
#         order = get_object_or_404(OrderItem, pk=pk)
#         order.delete()
#         return Response({'msg': ""}, status=status.HTTP_204_NO_CONTENT)

# class BillView(ListCreateAPIView):
#     def get_serializer_class(self):
#         if self.request.method == 'GET':
#             return BillSerializer
#         elif self.request.method == 'POST':
#             return BillCreateSerializer
        
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

#     def get_queryset(self):
#         queryset = Bill.objects.filter(user=self.request.user)
#         return queryset

# class BillDetailView(RetrieveAPIView):
#     queryset = Bill.objects.all()
#     serializer_class = BillDetailSerializer
#     def get_object(self):
#         identifier = self.kwargs['pk']
#         # try:
#         obj = self.get_queryset().get(pk=identifier, user=self.request.user.id)        
#         # ! 해당 주소가 없을 때, 예외처리 어떻게 해야할지 방법 찾아야함.
#         # except Bill.DoesNotExist:
#         #     raise Response({'msg': "해당 주문내역이 없습니다."}, status=status.HTTP_404_NOT_FOUND)
#         return obj
