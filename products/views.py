from rest_framework.views import APIView
from rest_framework.generics import (
    get_object_or_404,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveUpdateAPIView,
    ListAPIView,
)
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    ProductListSerializer,
    CategoryDetailSerializer,
    CategoryListSerializer,
    ProductDetailSerializer,
    ReviewSerializer,
    ReviewDetailSerializer,
)
from rest_framework.permissions import IsAuthenticated
from .models import Product, Category, Review
from users.models import Seller
from rest_framework.permissions import IsAuthenticated
from config.permissions_ import IsApprovedSeller, IsReadOnly


class CategoryListAPIView(ListCreateAPIView):
    """카테고리 조회, 생성"""

    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer


class CategoryDetailAPIView(RetrieveAPIView):
    """카테고리 상세 조회"""

    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer
    lookup_field = "id"


class ProductListAPIView(ListCreateAPIView):
    """상품 전체 조회, 생성 / 특정 판매자의 상품 전체 조회"""

    permission_classes = [(IsAuthenticated & IsApprovedSeller) | IsReadOnly]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        # url에서 user_id 존재하면 필터링, 없으면 전체
        if user_id:
            seller = get_object_or_404(Seller, user=user_id)
            queryset = Product.objects.filter(seller=seller.id)
        else:
            queryset = Product.objects.all()
        return queryset

    def perform_create(self, serializer):
        seller = get_object_or_404(Seller, user=self.request.user)
        serializer.save(seller=seller)


class ProductDetailAPIView(RetrieveUpdateDestroyAPIView):
    """상품 상세 조회, 수정, 삭제 (Retrieve 상속에서 수정됨)"""

    permission_classes = [(IsAuthenticated & IsApprovedSeller) | IsReadOnly]
    serializer_class = ProductDetailSerializer
    queryset = Product.objects.all()

    def perform_update(self, serializer):
        seller = get_object_or_404(Seller, user=self.request.user)
        serializer.save(seller=seller)


class ReviewView(ListCreateAPIView):
    """리뷰 조회, 생성"""

    serializer_class = ReviewSerializer

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        queryset = Review.objects.filter(product_id=product_id)
        return queryset

    def perform_create(self, serializer):
        product = Product.objects.get(id=self.kwargs.get("product_id"))
        serializer.save(user=self.request.user, product=product)


class ReviewDetailView(RetrieveUpdateAPIView):
    """리뷰 상세 조회, 수정"""

    serializer_class = ReviewDetailSerializer

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        queryset = Review.objects.filter(product_id=product_id)
        return queryset


class MyReviewView(ListAPIView):
    """내 리뷰 조회"""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    lookup_field = "user_id"
