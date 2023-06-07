from rest_framework.views import APIView 
from rest_framework import generics
from rest_framework.response import Response
from .models import Product, Category
from .serializers import CategoryListSerializer,ProductListSerializer, ProductDetailSerializer


class CategoryListAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer


class CategoryDetailAPIView(APIView):
    def get(self, request, name):
        products = Product.objects.filter(category__name=name)
        serializer = ProductDetailSerializer(products, many=True)
        return Response(serializer.data)


class ProductListAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer


class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    lookup_field = 'name'
