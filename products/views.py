from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from .serializers import (
    ProductListSerializer,
    CategoryDetailSerializer,
    CategoryListSerializer,
    ProductDetailSerializer,
    ReviewSerializer,
    ReviewDetailSerializer,
)
from rest_framework import status
from .models import Product, Category, Review
from rest_framework.permissions import IsAuthenticated


class CategoryListAPIView(generics.ListCreateAPIView):
    """카테고리 조회, 생성"""

    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer


class CategoryDetailAPIView(generics.RetrieveAPIView):
    """카테고리 상세 조회"""

    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer
    lookup_field = "id"


class ProductListAPIView(generics.ListCreateAPIView):
    """상품 전체 조회, 생성"""

    queryset = Product.objects.all()
    serializer_class = ProductListSerializer


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """상품 상세 조회, 수정, 삭제 (Retrieve 상속에서 수정됨)"""

    serializer_class = ProductDetailSerializer
    queryset = Product.objects.all()
    lookup_field = "id"


class ReviewView(generics.ListCreateAPIView):
    """리뷰 조회, 생성"""

    serializer_class = ReviewSerializer

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        queryset = Review.objects.filter(product_id=product_id)
        return queryset


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """리뷰 상세 조회, 수정, 삭제"""

    serializer_class = ReviewDetailSerializer

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        queryset = Review.objects.filter(product_id=product_id)
        return queryset


class MyReviewView(generics.ListAPIView):
    """내 리뷰 조회"""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    lookup_field = "user_id"
