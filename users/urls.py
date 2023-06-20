from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .social import KakaoLogin, GoogleLogin, NaverLogin
from .views import (
    UserAPIView,
    GetEmailAuthCodeAPIView,
    DeliveryAPIView,
    UpdateDeliveryAPIView,
    SellerAPIView,
    SellerPermissionAPIView,
    UserProfileAPIView,
    CustomTokenObtainPairView,
    PointView,
    PointStaticView,
    SubscribeView,
    ReviewListAPIView,
    WishListAPIView,
    PointAttendanceView,
    PointCheckoutView, 
    PointImpAjaxView,
    PhoneVerificationAPIView,
)
from .orderviews import (
    CartView,
    CartDetailView,
    BillView,
    BillDetailView,
    OrderCreateView,
    OrderListView,
    OrderDetailView,
    StatusCategoryView,
)
from .subscription import SubscribecheckView

urlpatterns = [
    # 회원 가입 비밀번호 찾기
    path("", UserAPIView.as_view(), name="user_view"),
    # 인증 코드 발급 받기
    path("get/auth_code/", GetEmailAuthCodeAPIView.as_view(), name="deliveries_view"),
    # 배송 정보 추가
    path(
        "create/delivery/<int:user_id>/",
        DeliveryAPIView.as_view(),
        name="create-delivery",
    ),
    # 배송 정보 수정 및 삭제
    path(
        "delivery/<int:delivery_id>/",
        UpdateDeliveryAPIView.as_view(),
        name="update-delivery",
    ),
    # 판매자 권한 신청 , 판매자 정보 수정 , 판매자 정보 삭제
    path("seller/", SellerAPIView.as_view(), name="seller-view"),
    # 판매자 정보 조회 , 관리자 권한으로 판매자 권한 부여, 또는 판매자 데이터 삭제(요청거절)
    path(
        "seller/permissions/<int:user_id>/",
        SellerPermissionAPIView.as_view(),
        name="seller-view",
    ),
    # 프로필 읽기, 회원정보 수정, 휴면 계정으로 전환
    path("profile/<int:user_id>/", UserProfileAPIView.as_view(), name="profile-view"),
    # SIMPLE JWT Token 발급
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    # refresh token 발급
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # 장바구니 조회
    path("carts/", CartView.as_view(), name="cart_view"),
    # 장바구니 삭제, 일괄삭제
    path("carts/delete/", CartView.as_view(), name="cart_delete_view"),
    # 장바구니 담기, 장바구니 수량 변경
    path("carts/<int:pk>/", CartDetailView.as_view(), name="cart_detail_view"),
    # 포인트 보기
    path(
        "points/<str:date>/statistic/",
        PointStaticView.as_view(),
        name="point_date_static",
    ),
    path("points/<str:date>/", PointView.as_view(), name="point_date_view"),
    # 출석용 포인트
    path("attendance/", PointAttendanceView.as_view(), name="point_attendance_view"),
    # # 텍스트리뷰용
    # path("text/", PointReviewView.as_view(), name="point_review_view"),
    # # 포토리뷰용
    # path("photo/", PointPhotoView.as_view(), name="point_photo_view"),
    # 구독
    path("subscribe/", SubscribeView.as_view(), name="subscribe_view"),
    # 주문 상태 생성
    path("status/", StatusCategoryView.as_view(), name="status_category_view"),
    # 주문 내역 생성, 조회
    path("bills/", BillView.as_view(), name="bill_view"),
    # 주문 내역 상세 조회
    path("bills/<int:pk>/", BillDetailView.as_view(), name="bill_detail_view"),
    # 주문 생성
    path(
        "bills/<int:bill_id>/orders/",
        OrderCreateView.as_view(),
        name="order_create_view",
    ),
    # 전체 주문 목록 조회
    path("orders/products/", OrderListView.as_view(), name="all_order_list_view"),
    # 판매자별 주문 목록 조회
    path(
        "orders/products/seller/<int:user_id>/",
        OrderListView.as_view(),
        name="seller_order_list_view",
    ),
    # 상품별 주문 목록 조회
    path(
        "orders/products/<int:product_id>/",
        OrderListView.as_view(),
        name="order_list_view",
    ),
    # 주문 상세 조회
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order_detail_view"),
    # 리뷰 좋아요 등록 및 취소, 좋아요 등록한 유저의 간략한 정보 불러오기
    path(
        "review/<int:review_id>/", ReviewListAPIView.as_view(), name="review-list-API"
    ),
    # 상품 찜  등록 및 취소, 찜 등록한 유저의 간략한 정보 불러오기
    path("wish/<int:product_id>/", WishListAPIView.as_view(), name="wish-list-API"),
    # 결제api
    path("payment/checkout/", PointCheckoutView.as_view(), name="point_checkout"),
    path("payment/validation/", PointImpAjaxView.as_view(), name="point_validation"),
    # # 상품 구매용 포인트 차감
    # path("pointpayment/", PointBuyView.as_view(), name="point_buy_view"),
    path("phone/verification/", PhoneVerificationAPIView.as_view(), name='phone_verification'),
    
    # 스케줄링
    path("scheduling/", SubscribecheckView.as_view(), name='subscribe_check'),
]

urlpatterns += [
    # 카카오 로그인
    path("kakao/login/", KakaoLogin.as_view(), name="kakao-login"),
    # 네이버 로그인
    path("naver/login/", NaverLogin.as_view(), name="naver-login"),
    # 구글 로그인
    path("google/login/", GoogleLogin.as_view(), name="google-login"),
]
