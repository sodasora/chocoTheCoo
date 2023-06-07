from django.shortcuts import get_object_or_404
from rest_framework.generics import get_object_or_404, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from models import CartItem

class CartView(ListCreateAPIView):
    queryset = CartItem.objects.all()
    # serializer_class = 

class CartItemView(RetrieveUpdateDestroyAPIView):
    queryset = CartItem.objects.all()
    # serializer_class = 