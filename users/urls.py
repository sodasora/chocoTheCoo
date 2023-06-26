from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .social import (
    KakaoLogin,
    GoogleLogin,
    NaverLogin,
)
from .views import (
    UserAPIView,
    EmailAuthenticationAPIView,
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
    UpdateUserInformationAPIView,
    FollowAPIView,
    GetDeliveryAPIView,

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
    StatusChangeView
)
from .subscription import SubscribecheckView


"""
User API
회원가입 및 인증, 로그인 및 소셜 로그인, 회원 정보 수정, 팔로우, 위시리스트, 좋아요
"""
urlpatterns = [
    # 회원 가입 , 회원 탈퇴 , 비밀번호 수정, 이메일 수정
    path("", UserAPIView.as_view(), name="user_view"),
    # 프로필, 통관 번호 수정
    path("update/information/", UpdateUserInformationAPIView.as_view(), name="update_information"),
    # 이메일 인증
    path("get/auth_code/", EmailAuthenticationAPIView.as_view(), name="email_authentication"),
    # 핸드폰 인증
    path("phone/verification/", PhoneVerificationAPIView.as_view(), name='phone_verification'),
    # 프로필 읽기
    path("profile/<int:user_id>/", UserProfileAPIView.as_view(), name="profile-view"),
    # 리뷰 좋아요 등록 및 취소, 좋아요 등록한 유저의 간략한 정보 불러오기
    path("review/<int:review_id>/", ReviewListAPIView.as_view(), name="review-list-API"),
    # 상품 찜  등록 및 취소, 찜 등록한 유저의 간략한 정보 불러오기
    path("wish/<int:product_id>/", WishListAPIView.as_view(), name="wish-list-API"),
    # 팔로우 / 언팔로우, 팔로우 사용자 정보 불러오기
    path("follow/<int:user_id>/", FollowAPIView.as_view(), name="follow-API"),
    # SIMPLE JWT Token 발급
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    # refresh token 발급
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # 카카오 로그인, 콜백 처리
    path("kakao/login/", KakaoLogin.as_view(), name="kakao-login"),
    # 구글 로그인 , 콜백 처리
    path("google/login/", GoogleLogin.as_view(), name="google-login"),
    # 네이버 로그인
    path("naver/login/", NaverLogin.as_view(), name="naver-login"),
]

"""
DeliveryAPI
배송 정보 CRUD
"""
urlpatterns += [
    # 배소 정보 읽기
    path("get/delivery/<int:user_id>/", GetDeliveryAPIView.as_view(), name="create-delivery"),
    # 배송 정보 추가
    path("create/delivery/", DeliveryAPIView.as_view(), name="create-delivery"),
    # 배송 정보 수정 및 삭제
    path("delivery/<int:delivery_id>/", UpdateDeliveryAPIView.as_view(), name="update-delivery"),
]

"""
SellerAPI
판매자 정보 CRUD
"""
urlpatterns += [
    # 판매자 권한 신청 , 판매자 정보 수정 , 판매자 정보 삭제
    path("seller/", SellerAPIView.as_view(), name="seller-view"),
    # 판매자 정보 조회 , 관리자 권한으로 판매자 권한 부여, 또는 판매자 데이터 삭제(요청거절)
    path("seller/permissions/<int:user_id>/", SellerPermissionAPIView.as_view(), name="seller-view"),
]

"""
OrderAPI
장바구니, 주문내역, 주문 상품 CRUD
"""
urlpatterns += [
    # 장바구니 담기, 조회
    path("carts/", CartView.as_view(), name="cart_view"),
    # 장바구니 삭제, 일괄삭제
    path("carts/delete/", CartView.as_view(), name="cart_delete_view"),
    # 장바구니 수량 변경
    path("carts/<int:pk>/", CartDetailView.as_view(), name="cart_detail_view"),
    # 주문 상태 생성
    path("status/", StatusCategoryView.as_view(), name="status_category_view"),
    # 주문 내역 생성, 조회
    path("bills/", BillView.as_view(), name="bill_view"),
    # 주문 내역 상세 조회
    path("bills/<int:pk>/", BillDetailView.as_view(), name="bill_detail_view"),
    # 주문 생성
    path("bills/<int:bill_id>/orders/",OrderCreateView.as_view(),name="order_create_view"),
    # 판매자별 주문 목록 조회
    path("orders/products/", OrderListView.as_view(), name="seller_order_list_view"),
    # 상품별 주문 목록 조회
    path("orders/products/<int:product_id>/",OrderListView.as_view(),name="order_list_view"),
    # 주문 상세 조회
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order_detail_view"),
    # 주문 상태 변경 ()
    path("orders/status/<int:pk>/", StatusChangeView.as_view(), name="status_change_view"),
]

"""
PointAPI
포인트 사용 및 적립, 
"""
urlpatterns += [
    # 포인트 보기
    path("points/<str:date>/statistic/",PointStaticView.as_view(),name="point_date_static"),
    path("points/<str:date>/", PointView.as_view(), name="point_date_view"),
    # 출석용 포인트
    path("attendance/", PointAttendanceView.as_view(), name="point_attendance_view"),
    # 구독
    path("subscribe/", SubscribeView.as_view(), name="subscribe_view"),
    # 결제api
    path("payment/checkout/", PointCheckoutView.as_view(), name="point_checkout"),
    path("payment/validation/", PointImpAjaxView.as_view(), name="point_validation"),
    # 스케줄링
    path("scheduling/", SubscribecheckView.as_view(), name='subscribe_check'),
]