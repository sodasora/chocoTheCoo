from rest_framework.permissions import BasePermission, IsAdminUser, SAFE_METHODS

# Admin유저만 CUD가능, 나머지는 Read Only
# ex) 카테고리 Create 등
class IsAdminUserOrReadOnly(IsAdminUser):
    def has_permission(self, request, view):
        is_admin = super().has_permission(request, view)
        return request.method in SAFE_METHODS or is_admin

# Seller 신청 O, 승인여부 상관없음
# ex) 판매자 마이페이지 조회 등
class IsSeller(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, "user_seller")

# Seller 신청 O, 승인됨
# ex) 상품 등록 등
class IsApprovedSeller(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_seller
    
# 배송정보가 등록된 유저만 사용가능
# ex) 상품 구매 등
class IsDeliveryRegistered(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, "deliveries_data")

# 통관번호가 등록된 유저만 사용가능
class IsPCCRegistered(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, "numbers")
