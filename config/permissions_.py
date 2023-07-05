from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied


# ReadOnly 사용 예시
# permission_class = [ReadOnly | IsAdminUser]
# => 어드민 유저는 CRUD모두 가능, 그 외 유저는 Read만 가능
#! 단독으로 사용하지 않는 것을 권장
class IsReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


# Seller 신청 O, 승인여부 상관없음
# ex) 판매자 마이페이지 조회 등
class IsSeller(BasePermission):
    message = "No Seller object related to User."

    def has_permission(self, request, view):
        return hasattr(request.user, "user_seller")


# Seller 신청 O, 승인됨
# ex) 상품 등록 등
class IsApprovedSeller(BasePermission):
    message = "User's is_seller is False(not approved)."

    def has_permission(self, request, view):
        return bool(request.user.is_seller)


# 배송정보가 등록된 유저만 사용가능
# ex) 상품 구매 등
class IsDeliveryRegistered(BasePermission):
    message = "No Delivery object related to User."

    def has_permission(self, request, view):
        return hasattr(request.user, "deliveries_data")


# 통관번호가 등록된 유저만 사용가능
class IsPCCRegistered(BasePermission):
    message = "Only Seller can access this resource"

    def has_permission(self, request, view):
        return bool(request.user.customs_code)
