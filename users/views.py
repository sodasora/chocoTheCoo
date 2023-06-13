from rest_framework import generics
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.utils import IntegrityError
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from .models import User, Delivery, Seller, Point, Subscribe
from products.models import Product, Review
from .validated import EmailService
from .cryption import AESAlgorithm
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    DeliverySerializer,
    ReadUserSerializer,
    SellerSerializer,
    PointSerializer,
    SubscriptionSerializer,
    GetWishListUserInfo,
    GetReviewUserListInfo,
    UserDetailSerializer,
    SubscriptionInfoSerializer,
)


class GetEmailAuthCodeAPIView(APIView):
    """
    이메일 인증코드 발송
    """

    def put(self, request):
        """
        인증 코드 이메일 발송 및 DB 저장
        """
        user = get_object_or_404(User, email=request.data["email"])
        auth_code = EmailService.get_authentication_code()
        user.auth_code = auth_code
        user.save()

        information = {
            "email": user.email,
            "context": {
                'subject_message': "Choco The Coo has sent you a verification code",
                'content_message': user.auth_code,
            }
        }
        EmailService.message_forwarding(**information)

        return Response({"msg": "인증 코드를 발송 했습니다."}, status=status.HTTP_200_OK)


class UserAPIView(APIView):
    """
    GET : 사용자 디테일 정보 불러오기
    POST : 회원가입
    PUT : 이메일 인증
    PATCH : 비밀번호 재 설정 (비밀번호 찾기 기능)
    """

    def get(self, request):
        """
        사용자 디테일 정보 불러오기  (복호화가 필요한 데이터 포함)
        """
        try:
            user = get_object_or_404(User, email=request.user.email)
        except AttributeError:
            return Response({"err": "로그인이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserDetailSerializer(user)
        decrypt_result = AESAlgorithm.decrypt_all(**serializer.data)
        return Response(decrypt_result, status=status.HTTP_200_OK)

    def post(self, request):
        """
        회원 가입
        """
        serializer = UserSerializer(data=request.data, context="create")
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"msg": "회원 가입 되었습니다. 계정 인증을 진행해 주세요."}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request):
        """
        회원 가입시 이메일 인증
        """
        user = get_object_or_404(User, email=request.data["email"])
        if user.auth_code is None:
            return Response(
                {"mrr": "먼저 인증코드를 발급받아주세요."}, status=status.HTTP_406_NOT_ACCEPTABLE
            )
        elif not user.auth_code == request.data["auth_code"]:
            return Response(
                {"err": "인증 코드가 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            user.is_active = True
            user.auth_code = None
            user.save()
            return Response({"msg": "인증 되었습니다."}, status=status.HTTP_200_OK)

    def patch(self, request):
        """
        비밀번호 재 설정(찾기 기능) or 휴면 계정 활성화 신청 응답
        """
        user = get_object_or_404(User, email=request.data["email"])
        if user.auth_code == "":
            return Response(
                {"msg": "먼저 인증코드를 발급받아주세요."}, status=status.HTTP_406_NOT_ACCEPTABLE
            )
        elif not user.auth_code == request.data["auth_code"]:
            return Response(
                {"err": "인증 코드가 올바르지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = UserSerializer(user, data=request.data, partial=True,context="update")
        if serializer.is_valid():
            serializer.save()
            user.auth_code = None
            user.is_active = True
            user.login_attempts_count = 0
            user.save()
            return Response({"msg": "비밀번호를 재 설정 했습니다."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    """
    GET : 마이페이지 정보 읽기
    PUT : 회원 정보 수정
    DELETE : 휴면 계정으로 전환
    """

    def get(self, request, user_id):
        """
        마이페이지 정보 읽어오기
        """
        user = get_object_or_404(User, id=user_id)
        serializer = ReadUserSerializer(user)
        total_plus_point = (
            Point.objects.filter(user_id=user.id)
            .filter(point_type_id__in=[1, 2, 3, 4, 5])
            .aggregate(total=Sum("point"))
        )
        total_minus_point = (
            Point.objects.filter(user_id=user.id)
            .filter(point_type_id=6)
            .aggregate(total=Sum("point"))
        )
        try:
            total_point = total_plus_point["total"] - total_minus_point["total"]
        except TypeError:
            total_point = (
                total_plus_point["total"]
                if total_plus_point["total"] is not None
                else 0
            )
        new_serializer_data = dict(serializer.data)
        new_serializer_data["total_point"] = total_point
        return Response(new_serializer_data, status=status.HTTP_200_OK)

    def put(self, request, user_id):
        """
        회원 정보 수정 (프로필 이미지, 닉네임, 통관번호, 이메일, 비밀번호)
        """
        user = get_object_or_404(User, id=user_id)
        if request.user != user:
            return Response({"err": "권한이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(
            user, data=request.data, partial=True, context="update"
        )
        if serializer.is_valid():
            serializer.save()
            user.login_attempts_count = 0
            user.save()
            return Response({"msg": "회원 정보를 수정 했습니다."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        """
        휴면 계정으로 전환
        """
        user = get_object_or_404(User, id=user_id)
        if request.user != user:
            return Response({"err": "권한이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = False
        user.save()
        return Response({"msg": "휴면 계정으로 전환 되었습니다."}, status=status.HTTP_200_OK)


class DeliveryAPIView(APIView):
    """
    GET : 사용자의 배송 정보들 읽기 (복호화)
    POST : 사용자의 배송 정보 기입
    """

    def get(self, request, user_id):
        """
        배송 정보들 읽기
        """
        user = get_object_or_404(User, id=user_id)
        serializer = DeliverySerializer(user.deliveries_data, many=True)
        decrypt_result = AESAlgorithm.decrypt_deliveries(serializer.data)
        return Response(decrypt_result, status=status.HTTP_200_OK)

    def post(self, request, user_id):
        """
        배송 정보 추가
        """
        user = get_object_or_404(User, id=user_id)
        if request.user != user:
            return Response({"err": "권한이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        deliveries_cnt = Delivery.objects.filter(user=user).count()
        if deliveries_cnt > 4:
            return Response(
                {"err": "배송 정보는 다섯개 까지 등록할 수 있습니다."}, status=status.HTTP_400_BAD_REQUEST
            )
        if request.data.get("postal_code") is not None:
            serializer = DeliverySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user)
                return Response({"msg": "배송 정보가 등록되었습니다."}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        return Response({"msg": "우편 번호 정보가 없습니다."}, status=status.HTTP_204_NO_CONTENT)


class UpdateDeliveryAPIView(APIView):
    """
    PUT : 사용자의 배송 정보 수정
    DELETE : 사용자의 배송 정보 삭제
    """

    def put(self, request, delivery_id):
        """
        배송 정보 수정
        """
        delivery = get_object_or_404(Delivery, id=delivery_id)
        if request.user == delivery.user:
            serializer = DeliverySerializer(delivery, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"msg": "배송 정보를 수정 했습니다."}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"err": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, delivery_id):
        """
        배송 정보 삭제
        """
        delivery = get_object_or_404(Delivery, id=delivery_id)
        if request.user == delivery.user:
            delivery.delete()
            return Response(
                {"msg": "배송 정보가 삭제 되었습니다."}, status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response({"err": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)


class SellerAPIView(APIView):
    """
    POST : 판매자 정보 기입과 동시에 권한 신청
    PUT : 사용자의 판매자 정보 수정
    DELETE : 사용자가 판매자 정보 삭제
    """

    def post(self, request):
        """
        판매자 정보 저장 및 권한 신청
        """
        try:
            user = get_object_or_404(User, email=request.user.email)
        except AttributeError:
            return Response({"err": "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer = SellerSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user)
                return Response(
                    {"msg": "판매자 권한을 성공적으로 신청했습니다. 검증 후에 승인 됩니다."},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        except IntegrityError:
            return Response(
                {"err": "이미 판매자 정보가 있습니다."}, status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request):
        """
        판매자 정보 수정
        """
        try:
            user = get_object_or_404(User, email=request.user.email)
        except AttributeError:
            return Response({"err": "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer = SellerSerializer(
                user.user_seller, data=request.data, partial=True
            )
        except Seller.DoesNotExist:
            return Response(
                {"err": "수정할 판매자 정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
            )
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "판매자 정보를 수정 했습니다."}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request):
        """
        판매자 정보 삭제
        """
        try:
            user = get_object_or_404(User, email=request.user.email)
        except AttributeError:
            return Response({"err": "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user.user_seller.delete()
        except Seller.DoesNotExist:
            return Response(
                {"err": "판매자 정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response({"msg": "판매자 정보를 삭제 했습니다."}, status=status.HTTP_204_NO_CONTENT)


class SellerPermissionAPIView(APIView):
    """
    GET : 사용자의 판매자 정보 읽기 (복호화)
    PATCH : 관리자가 판매자 권한 승인 (사용자의 is_seller 필드 True로 변경)
    DELETE : 관리자가 판매자 권한 거절 (사용자의 판매자 정보 삭제)
    """

    def get(self, request, user_id):
        """
        판매자 정보 읽기
        """
        user = get_object_or_404(User, id=user_id)
        try:
            serializer = SellerSerializer(user.user_seller)
        except Seller.DoesNotExist:
            return Response(
                {"err": "판매자 정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
            )
        decrypt_result = AESAlgorithm.decrypt_all(**serializer.data)
        return Response(decrypt_result, status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        """
        판매자 권한 승인
        """
        try:
            admin = get_object_or_404(User, email=request.user.email)
        except AttributeError:
            return Response({"err": "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        if not admin.is_admin:
            return Response(
                {"err": "올바른 접근 방법이 아닙니다."}, status=status.HTTP_401_UNAUTHORIZED
            )
        user = get_object_or_404(User, id=user_id)
        user.is_seller = True
        information = {
            "email": user.email,
            "context": {
                'subject_message': "관리자가 판매자 권한을 승인 했습니다.",
                'content_message': "사용자분께서 이제 판매자로서 활동하실 수 있습니다.",
            }
        }
        EmailService.message_forwarding(**information)
        user.save()
        return Response({"msg": "판매자 권한을 승인했습니다."}, status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, user_id):
        """
        판매자 정보 삭제
        request
         - admin accesstoken
         - "msg" : "거절 사유"
        """
        try:
            admin = get_object_or_404(User, email=request.user.email)
        except AttributeError:
            return Response({"err": "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        if not admin.is_admin:
            return Response(
                {"err": "올바른 접근 방법이 아닙니다."}, status=status.HTTP_401_UNAUTHORIZED
            )
        user = get_object_or_404(User, id=user_id)
        try:
            information = {
                "email": user.email,
                "context": {
                    'subject_message': "관리자가 판매자 권한을 거절 했습니다.",
                    'content_message': request.data.get('msg'),
                }
            }
            EmailService.message_forwarding(**information)
            user.user_seller.delete()
            return Response({"msg": "판매자 정보를 삭제 했습니다."}, status=status.HTTP_204_NO_CONTENT)
        except Seller.DoesNotExist:
            return Response({"err": "판매자 정보가 없습니다."}, status=status.HTTP_410_GONE)




class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST : 로그인 , access token 발급
    """

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, email=request.data.get("email"))
        if user.is_active is False:
            return Response({"msg": "휴면 계정입니다."}, status=status.HTTP_204_NO_CONTENT)
        elif user.login_attempts_count >= 5:
            return Response({'msg': "비밀 번호 입력 회수가 초과 되었습니다."}, status=status.HTTP_424_FAILED_DEPENDENCY)
        try:
            if check_password(request.data.get("password"), user.password):
                user.login_attempts_count = 0
                user.save()

                response = super().post(request, *args, **kwargs)
                refresh_token = response.data["refresh"]
                access_token = response.data["access"]
                data_dict = {
                    "refresh": refresh_token,
                    "access": access_token,
                }
                return Response(data_dict, status=status.HTTP_200_OK)
            else:
                user.login_attempts_count += 1
                user.save()
                return Response(5 - user.login_attempts_count, status=status.HTTP_401_UNAUTHORIZED)
        except TypeError:
            return Response({"err": "입력값이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)


class WishListAPIView(APIView):
    """
    GET : 상품 찜 등록한 유저 정보 불러오기,
    POST : 상품 찜 등록 및 취소
    """

    def get(self, request, product_id):
        """
        상품을 찜 등록한 사용자 정보들 불러오기
        """
        product = get_object_or_404(Product, id=product_id)
        serializer = GetWishListUserInfo(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, product_id):
        """
        상품 찜 등록 및 취소
        """
        user = get_object_or_404(User, email=request.user.email)
        product = get_object_or_404(Product, id=product_id)
        if product in user.product_wish_list.all():
            user.product_wish_list.remove(product)
            return Response(
                {"message": "상품 찜 등록을 취소 했습니다."}, status=status.HTTP_204_NO_CONTENT
            )
        else:
            user.product_wish_list.add(product)
            return Response(
                {"message": "상품을 찜 등록 했습니다."}, status=status.HTTP_201_CREATED
            )


class ReviewListAPIView(APIView):
    """
    GET : 리뷰 좋아요 등록한 유저 정보 불러오기,
    POST : 리뷰 좋아요 등록 및 취소
    """

    def get(self, request, review_id):
        """
        리뷰를 좋아요 등록한 사용자 정보들 불러오기
        """
        review = get_object_or_404(Review, id=review_id)
        serializer = GetReviewUserListInfo(review)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, review_id):
        """
        리뷰 좋아요 등록 및 취소
        """
        user = get_object_or_404(User, email=request.user.email)
        review = get_object_or_404(Review, id=review_id)
        if review in user.review_like.all():
            user.review_like.remove(review)
            return Response(
                {"message": "리뷰 좋아요를 취소 했습니다."}, status=status.HTTP_204_NO_CONTENT
            )
        else:
            user.review_like.add(review)
            return Response(
                {"message": "리뷰 좋아요를 등록 했습니다."}, status=status.HTTP_201_CREATED
            )


"""포인트"""
# 날짜별 포인트 보기
class PointView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PointSerializer

    def get_queryset(self):
        date = self.kwargs.get("date")
        queryset = Point.objects.filter(user=self.request.user, date=date)
        return queryset


# 통계
class PointStaticView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        # 포인트 총합 계산
        """포인트 종류: 출석(1), 텍스트리뷰(2), 포토리뷰(3), 구매(4), 충전(5), 구독권이용료(6)"""
        day_plus_point = (
            Point.objects.filter(user_id=request.user.id)
            .filter(point_type__in=[1,2,3,5])
            .filter(date=date)
            .aggregate(total=Sum("point"))
        )
        day_minus_point = (
            Point.objects.filter(user_id=request.user.id)
            .filter(point_type__in=[4,6])
            .filter(date=date)
            .aggregate(total=Sum("point"))
        )
        plus_point = (
            day_plus_point["total"] if day_plus_point["total"] is not None else 0
        )
        minus_point = (
            day_minus_point["total"] if day_minus_point["total"] is not None else 0
        )
        day_total_point = plus_point - minus_point
        month_plus_point = (
            Point.objects.filter(user_id=request.user.id)
            .filter(point_type__in=[1,2,3,5])
            .filter(date__month=timezone.now().date().month)
            .aggregate(total=Sum("point"))
        )
        month_minus_point = (
            Point.objects.filter(user_id=request.user.id)
            .filter(point_type__in=[4,6])
            .filter(date__month=timezone.now().date().month)
            .aggregate(total=Sum("point"))
        )
        month_plus = (
            month_plus_point["total"] if month_plus_point["total"] is not None else 0
        )
        month_minus = (
            month_minus_point["total"] if month_minus_point["total"] is not None else 0
        )
        month_total_point = month_plus - month_minus

        total_plus_point = (
            Point.objects.filter(user_id=request.user.id)
            .filter(point_type__in=[1,2,3,5])
            .aggregate(total=Sum("point"))
        )
        total_minus_point = (
            Point.objects.filter(user_id=request.user.id)
            .filter(point_type__in=[4,6])
            .aggregate(total=Sum("point"))
        )
        try:
            total_point = total_plus_point["total"] - total_minus_point["total"]
        except TypeError:
            total_point = (
                total_plus_point["total"]
                if total_plus_point["total"] is not None
                else 0
            )

        return Response(
            {
                "day_plus": plus_point,
                "day_minus": minus_point,
                "day_total_point": day_total_point,
                "month_total_point": month_total_point,
                "total_point": total_point,
            },
            status=status.HTTP_200_OK,
        )


"""포인트 종류: 출석(1)"""
class PointAttendanceView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PointSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, point_type_id=1, point=100)

    def get_queryset(self):
        queryset = Point.objects.filter(point_type=1, user=self.request.user, date=timezone.now().date())
        return queryset


"""포인트 종류: 텍스트리뷰(2)"""
class PointReviewView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PointSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, point_type_id=2, point=50)
    

"""포인트 종류: 포토리뷰(3)"""
class PointPhotoView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PointSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, point_type_id=3, point=100)


# """포인트 종류: 구매(4)"""
# class PointBuyView(generics.CreateAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = PointSerializer
    
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user, point_type_id=4)
        

# """포인트 종류: 충전(5)"""
# class PointChargeView(generics.CreateAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = PointSerializer
    
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user, point_type_id=5)
        

"""포인트 종류: 구독권이용료(6)"""
class PointServiceView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PointSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, point_type_id=6, point=9900)
        


"""구독"""
class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    # 구독 정보 가져오기
    def get(self, request):
        subscription = get_object_or_404(Subscribe, user_id=request.user.id)
        serializer = SubscriptionInfoSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 구독 최초 생성
    def post(self, request):
        serializer = SubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            newmonth = int(timezone.now().date().month) + 1
            serializer.save(user=request.user, next_payment=str(timezone.now().date().year) + "-" + str(newmonth) + "-" + str(timezone.now().date().day))
            return Response({"message": "성공!"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 구독해지 및 복구
    def patch(self, request):
        subscription = get_object_or_404(Subscribe, user_id=request.user.id)
        if subscription.subscribe == True:
            subscription.subscribe = False
            subscription.save()
            return Response({"message": "해지"}, status.HTTP_200_OK)
        else:
            subscription.subscribe = True
            if timezone.now().date().month == 12:
                newmonth = 1
            else:
                newmonth = int(timezone.now().date().month) + 1
            subscription.next_payment = str(timezone.now().date().year) + "-" + str(newmonth) + "-" + str(timezone.now().date().day)
            subscription.save()
            return Response({"message": "성공!"}, status.HTTP_200_OK)