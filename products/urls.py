from django.urls import path
from . import views


urlpatterns = [
    path('categories/', views.CategoryListAPIView.as_view(), name='category-list'),
    path('categories/<str:name>', views.CategoryDetailAPIView.as_view(), name='category-detail'),
    path('products/', views.ProductListAPIView.as_view(), name='product-list'),
    path('products/<str:name>', views.ProductDetailAPIView.as_view(), name='product-detail'),
]