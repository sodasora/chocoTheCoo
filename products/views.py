from rest_framework.views import APIView
from rest_framework.generics import (
    get_object_or_404,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveUpdateAPIView,
    ListAPIView,
)
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    ProductListSerializer,
    CategoryListSerializer,
    ProductDetailSerializer,
    ReviewSerializer,
    ReviewDetailSerializer,
    GetProductDetailSerializer,
)
from users.serializers import PointSerializer
from rest_framework.permissions import IsAuthenticated
from .models import Product, Category, Review
from users.models import Seller, User
from rest_framework.permissions import IsAuthenticated
from config.permissions_ import IsApprovedSeller, IsReadOnly
from rest_framework.pagination import PageNumberPagination
from math import ceil
from django.db.models import Avg, Count, Q


# 페이지네이션


class ProductPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = "page_size"
    max_page_size = 10000


class CategoryListAPIView(ListAPIView):
    """카테고리 조회"""

    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer


class AllProductListAPIView(ListAPIView):
    """특정 판매자의 상품 전체 조회"""

    permission_classes = [(IsAuthenticated & IsApprovedSeller) | IsReadOnly]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        queryset = Product.objects.filter(seller=user_id)
        return queryset


class ProductListAPIView(ListCreateAPIView):
    """상품 전체 조회, 필터링, 검색"""

    permission_classes = [(IsAuthenticated & IsApprovedSeller) | IsReadOnly]
    serializer_class = ProductListSerializer
    pagination_class = ProductPagination

    def get_queryset(self):
        filters = Q()
        params = self.request.query_params

        if seller := params.get("user_id"):
            filters &= Q(seller__user_id=seller)

        if search := params.get("search"):
            filters &= Q(name__contains=search) | Q(content__contains=search)

        if category := params.get("category"):
            filters &= Q(category__id=category)

        queryset = Product.objects.filter(filters).order_by("-created_at")

        if ordering := params.get("ordering"):
            queryset = ordering_queryset(queryset, ordering)

        return queryset

    def perform_create(self, serializer):
        seller = get_object_or_404(Seller, user=self.request.user)
        serializer.save(seller=seller)


def ordering_queryset(queryset, ordering):
    """쿼리셋 정렬 함수"""
    orderings = {
        "popularity": queryset.annotate(num_wishlists=Count("wish_lists")).order_by(
            "-num_wishlists"
        ),
        "stars": queryset.annotate(stars=Avg("product_reviews__star")).order_by(
            "-stars"
        ),
        "expensive": queryset.order_by("-price"),
        "cheap": queryset.order_by("price"),
    }
    return orderings[ordering]


class SellerProductListAPIView(ListAPIView):
    """특정 판매자 상품 전체 조회, 생성"""

    permission_classes = [(IsAuthenticated & IsApprovedSeller) | IsReadOnly]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return Product.objects.filter(seller=user_id).order_by("-created_at")


class ProductDetailAPIView(RetrieveUpdateDestroyAPIView):
    """상세 조회, 수정, 삭제 (Retrieve 상속에서 수정됨)"""

    permission_classes = [(IsAuthenticated & IsApprovedSeller) | IsReadOnly]
    queryset = Product.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return GetProductDetailSerializer
        else:
            return ProductDetailSerializer

    def perform_update(self, serializer):
        seller = get_object_or_404(Seller, user=self.request.user)
        serializer.save(seller=seller)


class ReviewView(ListCreateAPIView):
    """리뷰 조회, 생성"""

    permission_classes = [IsAuthenticated | IsReadOnly]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        queryset = Review.objects.filter(product_id=product_id)
        return queryset

    def perform_create(self, serializer):
        product = Product.objects.get(id=self.kwargs.get("product_id"))
        if self.request.data.get("image"):
            point = ceil(product.price * 0.05)
            point_type = 3
        else:
            point = ceil(product.price * 0.01)
            point_type = 2

        data = {"point": point}
        point_serializer = PointSerializer(data=data)
        point_serializer.save(user=self.request.user, point_type_id=point_type)
        serializer.save(user=self.request.user, product=product)


class ReviewDetailView(RetrieveUpdateAPIView):
    """리뷰 상세 조회, 수정"""

    permission_classes = [IsAuthenticated]  # 추가예정
    serializer_class = ReviewDetailSerializer

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        queryset = Review.objects.filter(product_id=product_id)
        return queryset


class MyReviewView(ListAPIView):
    """내 리뷰 조회"""

    permission_classes = [IsAuthenticated]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        queryset = Review.objects.filter(user=self.request.user)
        return queryset
