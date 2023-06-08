from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views, orderviews

urlpatterns = [
    # 회원 가입 비밀번호 찾기
    path('', views.UserAPIView.as_view(), name='user_view'),
    # 인증 코드 발급 받기
    path('get/auth_code/', views.GetEmailAuthCodeAPIView.as_view(), name='deliveries_view'),
    # 배송 정보 추가
    path('create/deliverie/<int:user_id>/', views.DeliveryAPIView.as_view(), name='create-deliverie'),
    # 배송 정보 수정 및 삭제
    path('deliverie/<int:deliverie_id>/', views.UpdateDeliveryAPIView.as_view(), name='update-deliverie'),
    # 판매자 권한 신청 , 판매자 정보 수정 , 판매자 정보 삭제
    path('seller/', views.SellerAPIView.as_view(), name='seller-view'),
    # 관리자 권한으로 판매자 권한 부여, 또는 판매자 데이터 삭제(요청거절)
    path('seller/permissions/<int:user_id>/', views.SellerPermissionAPIView.as_view(), name='seller-view'),
    # 프로필 읽기, 회원정보 수정, 휴면 계정으로 전환
    path('profile/<int:user_id>/', views.UserProfileAPIView.as_view(), name='profile-view'),
    # SIMPLE JWT Token 발급
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    # refresh token 발급
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # 장바구니 조회
    path("carts/", orderviews.CartView.as_view(), name='cart_view'),
    # 장바구니 담기, 장바구니 수량 변경, 삭제
    path("carts/<int:cart_item_id>/", orderviews.CartDetailView.as_view(), name='cart_detail_view'),
    # 포인트
    path('<int:user_id>/points/', views.PointView.as_view(), name='point_view'),
    path('<int:user_id>/points/<str:date>', views.PointDateView.as_view(), name='point_date_view'),
    # 구독
    path('subscribe/',views.SubscribeView.as_view(), name="subscribe_view"),
    # 주문 내역 생성, 조회
    path('bills/', orderviews.BillView.as_view(), name="bill_view"),
    # 주문 내역 상세 조회
    path('bills/<int:pk>/', orderviews.BillDetailView.as_view(), name="bill_detail_view"),
    # 주문 생성
    path("bills/<int:bill_id>/orders/", orderviews.OrderCreateView.as_view(), name='order_create_view'),
    # 주문 목록 조회
    path("orders/products/<int:product_id>/", orderviews.OrderListView.as_view(), name='order_list_view'),
    # 주문 상세 조회
    path("orders/<int:pk>/", orderviews.OrderDetailView.as_view(), name='order_detail_view'),
]
