from django.urls import path
from .views import (
    CategoryListAPIView,
    ProductListAPIView,
    ProductDetailAPIView,
    ReviewView,
    ReviewDetailView,
    MyReviewView,
    AllProductListAPIView,
    MyProductReview
)

"""
ProductAPI
상품 CRUD, 검색, 필터링, 정렬
"""
urlpatterns = [
    # 특정 판매자의 상품 페이지네이션 없이 전체 조회
    path("seller/<int:user_id>/all/", AllProductListAPIView.as_view(), name="seller-product-list-all"),
    # 상품 전체 조회
    path("", ProductListAPIView.as_view(), name="product-list"),
    # 상품 상세 조회
    path("<int:pk>/", ProductDetailAPIView.as_view(), name="product-detail"),
]

"""
ReviewAPI
리뷰 CRUD
"""
urlpatterns += [
    # 리뷰 조회, 생성
    path("<int:product_id>/reviews/", ReviewView.as_view(), name="review_view"),
    # 리뷰 상세 조회, 수정, 삭제
    path("<int:product_id>/reviews/<int:pk>/", ReviewDetailView.as_view(), name="review_detail_view"),
    # 유저의 리뷰 간단조회
    path("mypage/reviews/", MyReviewView.as_view(), name="myreview_view"),
    # 제품의 유저 리뷰 조회
    path("mypage/<int:product_id>/reviews/", MyProductReview.as_view(), name="my_product_review"),
]

"""
CategoryAPI
카테고리 조회
"""
urlpatterns += [
    # 카테고리 조회
    path("categories/", CategoryListAPIView.as_view(), name="category-list"),
]