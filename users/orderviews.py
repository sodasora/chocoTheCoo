from rest_framework.generics import get_object_or_404, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import CartItem
from .orderserializers import CartListCreateSerializer, CartUpdateDestroySerializer

class CartView(ListCreateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartListCreateSerializer

class CartDetailView(RetrieveUpdateDestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartUpdateDestroySerializer