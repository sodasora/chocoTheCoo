from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import generics
from .serializers import *
from rest_framework import status
from .models import Product, Category, Review
from rest_framework.permissions import IsAuthenticated

class CategoryListAPIView(generics.ListCreateAPIView):
    """ 카테고리 조회, 생성 """
    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer

class CategoryDetailAPIView(APIView):
    def get(self, request, name):
        products = Product.objects.filter(category__name=name)
        serializer = ProductDetailSerializer(products, many=True)
        return Response(serializer.data)


class ProductListAPIView(generics.ListCreateAPIView):
    """상품 전체 조회, 생성"""
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """상품 상세 조회, 수정, 삭제 (Retrieve 상속에서 수정됨)"""
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer


class ReviewView(generics.ListCreateAPIView):
    """ 리뷰 조회, 생성 """
    permission_classes = [IsAuthenticated]
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """ 리뷰 상세 조회, 수정, 삭제 """
    permission_classes = [IsAuthenticated]
    queryset = Review.objects.all()
    serializer_class = ReviewDetailSerializer


class MyReviewView(generics.ListAPIView):
    """ 내 리뷰 조회 """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    lookup_field = 'user_id'