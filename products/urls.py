from django.urls import path
from . import views


urlpatterns = [
    path('categories/', views.CategoryListAPIView.as_view(), name='category-list'),
    path('categories/<str:name>', views.CategoryDetailAPIView.as_view(), name='category-detail'),
    path('products/', views.ProductListAPIView.as_view(), name='product-list'),
    path('products/<str:name>', views.ProductDetailAPIView.as_view(), name='product-detail'),
        # 리뷰 조회, 생성
    path('<int:product_id>/reviews/', views.ReviewView.as_view(), name='review_view'),
    # 리뷰 상세 조회, 수정, 삭제
    path('<int:product_id>/reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail_view'),
    # 유저의 리뷰 간단조회
    path('mypage/reviews/<int:user_id>/', views.MyReviewView.as_view(), name='myreview_view'),
]