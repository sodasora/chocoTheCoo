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
        if cart:
            cart.count += 1
            cart.save()
            return Response({'msg': "장바구니에 추가되었습니다."}, status=status.HTTP_200_OK)
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': "장바구니에 추가되었습니다."}, status=status.HTTP_201_CREATED)
        return Response({"err":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class CartDetailView(APIView):
    # def get(self, request, pk):
    #     cart = get_object_or_404(CartItem, pk=pk)
    #     serializer = CartDetailSerializer(cart)
    #     return Response(serializer.data)

    def put(self, request, pk):
        # patch로 할 수 있나??? 바뀌는 것은 수량밖에 없음.
        cart = get_object_or_404(CartItem, pk=pk)
        serializer = CartDetailSerializer(cart, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': "장바구니에 추가되었습니다."}, status=status.HTTP_200_OK)
        return Response({"err":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        cart = get_object_or_404(CartItem, pk=pk)
        cart.delete()
        return Response({'msg': "장바구니 삭제"}, status=status.HTTP_204_NO_CONTENT)
    
# class OrderView(APIView):
#     def get(self, request):
#         order = OrderItem.objects.filter(user=request.user)
#         serializer = OrderItemSerializer(order, many=True)
#         return Response(serializer.data)
    
#     def post(self, request):
#         serializer = OrderItemSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response({'msg': ""}, status=status.HTTP_201_CREATED)
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
#     queryset = Bill.objects.all()
#     serializer_class = BillSerializer

# class BillDetailView(RetrieveAPIView):
#     queryset = Bill.objects.all()
#     serializer_class = BillDetailSerializer

