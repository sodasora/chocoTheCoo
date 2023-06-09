from django.urls import path
from .views import (CategoryListAPIView, CategoryDetailAPIView, ProductListAPIView,
                   ProductDetailAPIView, ReviewView, ReviewDetailView, MyReviewView,)

urlpatterns = [
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path('categories/<int:id>/', CategoryDetailAPIView.as_view(), name='category-detail'),
    path('', ProductListAPIView.as_view(), name='product-list'),
    path('<int:id>/', ProductDetailAPIView.as_view(), name='product-detail'),
        # 리뷰 조회, 생성
    path('<int:product_id>/reviews/', ReviewView.as_view(), name='review_view'),
    # 리뷰 상세 조회, 수정, 삭제
    path('<int:product_id>/reviews/<int:pk>/', ReviewDetailView.as_view(), name='review_detail_view'),
    # 유저의 리뷰 간단조회
    path('mypage/reviews/<int:user_id>/', MyReviewView.as_view(), name='myreview_view'),
]