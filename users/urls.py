from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    # 회원 가입 비밀번호 찾기
    path('', views.UserAPIView.as_view(), name='user_view'),
    # 인증 코드 발급 받기
    path('get/auth_code/', views.GetEmailAuthCodeAPIView.as_view(), name='deliveries_view'),
    # 배송 정보 추가
    path('create/deliverie/<int:user_id>/', views.DeliveryAPIView.as_view(), name='create-deliverie'),
    # 배송 정보 수정 및 삭제
    path('deliverie/<int:delivery_id>/', views.UpdateDeliveryAPIView.as_view(), name='update-deliverie'),
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
]
