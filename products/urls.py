from django.urls import path
from .views import (
    CategoryListAPIView,
    CategoryDetailAPIView,
    ProductListAPIView,
    ProductDetailAPIView,
    ReviewView,
    ReviewDetailView,
    MyReviewView,
    AllProductListAPIView,
)

urlpatterns = [
    # 카테고리 조회, 생성
    path("categories/", CategoryListAPIView.as_view(), name="category-list"),
    # 카테고리 상세 조회
    path(
        "categories/<int:id>/", CategoryDetailAPIView.as_view(), name="category-detail"
    ),
    # 특정 판매자의 상품 페이지네이션 없이 전체 조회
    path("seller/<int:user_id>/all/", AllProductListAPIView.as_view(), name="seller-product-list-all"),
    # 특정 판매자의 상품 전체 조회
    path("seller/<int:user_id>/", ProductListAPIView.as_view(), name="seller-product-list"),
    # 상품 전체 조회
    path("", ProductListAPIView.as_view(), name="product-list"),
    # 상품 상세 조회
    path("<int:pk>/", ProductDetailAPIView.as_view(), name="product-detail"),
    # 리뷰 조회, 생성
    path("<int:product_id>/reviews/", ReviewView.as_view(), name="review_view"),
    # 리뷰 상세 조회, 수정, 삭제
    path(
        "<int:product_id>/reviews/<int:pk>/",
        ReviewDetailView.as_view(),
        name="review_detail_view",
    ),
    # 유저의 리뷰 간단조회
    path("mypage/reviews/<int:user_id>/", MyReviewView.as_view(), name="myreview_view"),
    #상품 검색
]
