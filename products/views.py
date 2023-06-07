from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework import generics
from .serializers import *
from rest_framework import status
from .models import Product, Category, Review


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


class ReviewView(generics.ListCreateAPIView):
    """ 리뷰 조회, 생성 """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """ 리뷰 상세 조회, 수정, 삭제 """
    queryset = Review.objects.all()
    serializer_class = ReviewDetailSerializer
