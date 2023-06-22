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
    GetProductDetailSerializer,
)
from rest_framework.permissions import IsAuthenticated
from .models import Product, Category, Review
from users.models import Seller
from rest_framework.permissions import IsAuthenticated
from config.permissions_ import IsApprovedSeller, IsReadOnly
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q


# 페이지네이션
class PostingPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = "page_size"
    max_page_size = 10000


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
    # pagination_class = PostingPagination

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        if user_id:
            # seller = get_object_or_404(Seller, user=user_id)
            queryset = Product.objects.filter(seller=user_id)
        else:
            queryset = Product.objects.all()

        keyword = self.request.query_params.get("search", None)
        ordering = self.request.query_params.get("ordering", None)
        category = self.request.query_params.get("category", None)

        if keyword is not None:
            queryset = queryset.filter(
                Q(name__contains=keyword) | Q(content__contains=keyword)
            )
        if category is not None:
            queryset = queryset.filter(category__id=category)

        if ordering == "recent":
            queryset = queryset.order_by("-created_at")
        elif ordering == "popularity":
            queryset = queryset.annotate(num_wishlists=Count("wish_lists")).order_by(
                "-num_wishlists"
            )
        elif ordering == "expensive":
            queryset = queryset.order_by("-price")
        return queryset

    def perform_create(self, serializer):
        seller = get_object_or_404(Seller, user=self.request.user)
        serializer.save(seller=seller)


class ProductDetailAPIView(RetrieveUpdateDestroyAPIView):
    """상세 조회, 수정, 삭제 (Retrieve 상속에서 수정됨)"""

    def get_serializer_class(self):
        if self.request.method == "GET":
            return GetProductDetailSerializer
        else:
            return ProductDetailSerializer

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
