from rest_framework import generics
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.utils import IntegrityError
from django.db.models import Sum
from datetime import timedelta
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
from django.views.generic import TemplateView
from products.models import Product, Review
from .validated import ValidatedData, EmailService
from .models import (
    User,
    Delivery,
    Seller,
    Point,
    Subscribe,
    PayTransaction,
    PhoneVerification,
)
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    DeliverySerializer,
    ReadUserSerializer,
    SellerSerializer,
    PointSerializer,
    SubscriptionSerializer,
    UserDetailSerializer,
    SubscriptionInfoSerializer,
    PhoneVerificationSerializer,
    UserUpdateCustomsCodeSerializer,
    UserUpdateProfileSerializer,
    UserUpdateEmailSerializer,
    UserUpdatePasswordSerializer,
    UserPasswordResetSerializer,
    GetSellersInformationListSerializer,
)


class EmailAuthenticationAPIView(APIView):
    """
    이메일 인증 기능 API
    """

    def post(self, request):
        """
        인증 코드 이메일 발송 및 DB 저장
        """
        user = get_object_or_404(User, email=request.data.get("email"))
        email_delivery_result = EmailService.send_email_verification_code(user, user.email, 'normal')
        if email_delivery_result is not True:
            return Response({"err": email_delivery_result[1]}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"msg": "Success"}, status=status.HTTP_200_OK)

    def put(self, request):
        """
        이메일 인증
        """

        user = get_object_or_404(User, email=request.data["email"])
        validate_result = ValidatedData.validated_email_verification_code(user, request.data.get('verification_code'),
                                                                          'normal')
        if validate_result is not True:
            # 이메일 인증 코드 유효성 검사 False 또는 status 코드 값을 반환
            return Response(
                {"err": validate_result[1]}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            user.is_active = True
            user.email_verification.verification_code = None
            user.save()
            user.email_verification.save()
            return Response(
                {"msg": "Success"}, status=status.HTTP_200_OK
            )

    def patch(self, request):
        """
        비밀번호 재 설정(찾기 기능) or 휴면 계정 활성화 신청 응답
        """

        user = get_object_or_404(User, email=request.data.get('email'))
        serializer = UserPasswordResetSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"msg": "Success"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


class PhoneVerificationAPIView(APIView):
    """
    휴대폰 인증 API
    """

    def put(self, request):
        """
        휴대폰 정보 등록 및 수정
        인증 코드 발급 받기
        """

        user = get_object_or_404(User, pk=request.user.pk)
        try:
            # 원투원 필드가 있다면 수정
            serializer = PhoneVerificationSerializer(
                user.phone_verification, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(
                    {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        except PhoneVerification.DoesNotExist:
            # 원투원 필드가 없다면 생성
            serializer = PhoneVerificationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user)
            else:
                return Response(
                    {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {"msg": "Success"}, status=status.HTTP_200_OK
        )

    def patch(self, request):
        """
        휴대폰 인증
        """

        user = get_object_or_404(User, pk=request.user.pk)
        validated_result = ValidatedData.validated_phone_verification(user, request.data.get('verification_numbers'))
        if validated_result is not True:
            return Response(
                {"err": validated_result[1]}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            user.phone_verification.verification_numbers = None
            user.phone_verification.is_verified = True
            user.phone_verification.save()
            return Response(
                {"msg": "Success"}, status=status.HTTP_200_OK
            )


class UserAPIView(APIView):
    """
    사용자 정보 API
    """

    def get(self, request):
        """
        사용자 디테일 정보 불러오기  (복호화가 필요한 데이터 포함)
        """

        user = get_object_or_404(User, pk=request.user.pk)
        serializer = UserDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        회원 가입
        """
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"msg": "Success"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request):
        """
        비밀 번호 정보 수정
        """

        user = get_object_or_404(User, pk=request.user.pk)
        serializer = UserUpdatePasswordSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"msg": "Success"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request):
        """
        통관 번호 수정
        """

        user = get_object_or_404(User, pk=request.user.pk)
        serializer = UserUpdateCustomsCodeSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"msg": "Success"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request):
        """
        휴면 계정으로 전환
        """

        user = get_object_or_404(User, pk=request.user.pk)
        user.is_active = False
        user.save()
        return Response(
            {"msg": "Success"}, status=status.HTTP_200_OK
        )


class UpdateUserInformationAPIView(APIView):
    """
    변경 이메일로 인증 메일 발송, 프로필 , 통관 번호 수정
    """

    def post(self, request):
        """
        이메일 변경 신청시, 해당 이메일로 인증 코드 발급
        """

        user = get_object_or_404(User, pk=request.user.pk)
        new_email = request.data.get('email')
        try:
            # 변공하고자 하는 이메일 정보가, 이미 가입된 이메일 정보일 경우
            User.objects.get(email=new_email)
            return Response({"err": f'validation failed'}, status=status.HTTP_409_CONFLICT)
        except User.DoesNotExist:
            email_delivery_result = EmailService.send_email_verification_code(user, new_email, 'change')
            if email_delivery_result is not True:
                # 이메일 정보 유효성 검사
                return Response({"err": email_delivery_result[1]}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # 변경할 이메일로 인증 코드 발송
                user.email_verification.new_email = new_email
                user.email_verification.save()
                return Response({"msg": "Success"}, status=status.HTTP_200_OK)

    def put(self, request):
        """
        이메일 정보 수정
        """

        user = get_object_or_404(User, pk=request.user.pk)
        serializer = UserUpdateEmailSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"msg": "Success"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request):
        """
        프로필 정보 수정
        """

        user = get_object_or_404(User, pk=request.user.pk)
        serializer = UserUpdateProfileSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"msg": "Success"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileAPIView(APIView):
    """
    프로필 정보 읽기
    """

    def get(self, request, user_id):
        """
        마이페이지의 프로필 정보 읽어오기
        """

        user = get_object_or_404(User, id=user_id)
        serializer = ReadUserSerializer(user)
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )


class DeliveryAPIView(APIView):
    """
    GET : 배송 정보 읽기
    POST : 사용자의 배송 정보 기입
    """

    def get(self, request):
        """
        배송 정보들 읽기
        """

        user = get_object_or_404(User, pk=request.user.pk)
        serializer = DeliverySerializer(user.deliveries_data, many=True)
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    def post(self, request):
        """
        배송 정보 추가
        """

        user = get_object_or_404(User, pk=request.user.pk)
        serializer = DeliverySerializer(data=request.data, context={'user': request.user})
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(
                {"msg": "Success"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )


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
            serializer = DeliverySerializer(delivery, data=request.data, context={'user': request.user})
            if serializer.is_valid():
                serializer.save()
                return Response({"msg": "Success"}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"err": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, delivery_id):
        """
        배송 정보 삭제
        """
        delivery = get_object_or_404(Delivery, id=delivery_id)
        if request.user == delivery.user:
            #
            delivery.delete()
            return Response(
                {"msg": "Success"}, status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response({"err": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)


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
        user = get_object_or_404(User, pk=request.user.pk)
        try:
            serializer = SellerSerializer(data=request.data, context={"user": user})
            if serializer.is_valid():
                serializer.save(user=user)
                return Response(
                    {"msg": "Success"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        except IntegrityError:
            # 이미 사업자 등록이 되어 있을 경우
            return Response(
                {"err": "Locked"}, status=status.HTTP_409_CONFLICT
            )

    def put(self, request):
        """
        판매자 정보 수정
        """

        user = get_object_or_404(User, pk=request.user.pk)

        try:
            serializer = SellerSerializer(
                user.user_seller, data=request.data, partial=True
            )
        except Seller.DoesNotExist:
            return Response(
                {"err": "Locked"}, status=status.HTTP_409_CONFLICT
            )
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "Success"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request):
        """
        판매자 정보 삭제
        """
        user = get_object_or_404(User, pk=request.user.pk)

        try:
            for follower in user.follower.all():
                follower.followings.remove(user)

            user.is_seller = False
            user.user_seller.delete()
            user.save()
        except Seller.DoesNotExist:
            return Response(
                {"err": "Locked"}, status=status.HTTP_409_CONFLICT
            )
        return Response(
            {"msg": "Success"}, status=status.HTTP_204_NO_CONTENT
        )


class GetSalesMemberApplicationDetails(APIView):
    def get(self, request):
        """
        판매 권한 신청 승인 대기중인 사용자 목록 뽑아 오기
        """

        admin = get_object_or_404(User, pk=request.user.pk)
        if admin.is_admin is not True:
            return Response(
                {"err": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN
            )
        else:
            # seller 원투원 필드가 존재하면서, 판매 회원 권한이 없는 사용자 목록
            sellesr_list = Seller.objects.filter(user__user_seller__isnull=False, user__is_seller=False)
            serializer = GetSellersInformationListSerializer(sellesr_list, many=True)

            return Response(
                serializer.data, status=status.HTTP_200_OK
            )


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
            serializer = SellerSerializer(user.user_seller, context={'request': request})
        except Seller.DoesNotExist:
            return Response(
                {"err": "not found"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    def patch(self, request, user_id):
        """
        판매자 권한 승인
        """
        admin = get_object_or_404(User, pk=request.user.pk)
        if not admin.is_admin:
            return Response(
                {"err": "Forbidden"}, status=status.HTTP_403_FORBIDDEN
            )
        user = get_object_or_404(User, id=user_id)
        user.is_seller = True
        user.save()

        subject_message = '관리자가 판매자 권한을 승인 했습니다.'
        content_message = "사용자분께서 이제 판매자로서 활동하실 수 있습니다."
        EmailService.message_forwarding(user.email, subject_message, content_message)

        return Response(
            {"msg": "Success"}, status=status.HTTP_200_OK
        )

    def delete(self, request, user_id):
        """
        판매자 정보 삭제
        request
         - admin accesstoken
         - "msg" : "거절 사유"
        """

        admin = get_object_or_404(User, pk=request.user.pk)
        if not admin.is_admin:
            return Response(
                {"err": "Forbidden"}, status=status.HTTP_403_FORBIDDEN
            )
        user = get_object_or_404(User, id=user_id)
        try:
            for follower in user.follower.all():
                follower.followings.remove(user)

            subject_message = '관리자가 판매자 권한을 거절 했습니다.'
            content_message = request.data.get('msg')
            EmailService.message_forwarding(user.email, subject_message, content_message)
            user.user_seller.delete()
            return Response(
                {"msg": "Success"}, status=status.HTTP_204_NO_CONTENT
            )
        except Seller.DoesNotExist:
            return Response(
                {"err": "not found"}, status=status.HTTP_404_NOT_FOUND
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST : 로그인 , access token 발급
    """
    serializer_class = CustomTokenObtainPairSerializer


class WishListAPIView(APIView):
    """
    POST : 상품 찜 등록 및 취소
    """

    def post(self, request, product_id):
        """
        상품 찜 등록 및 취소
        """
        user = get_object_or_404(User, pk=request.user.pk)
        product = get_object_or_404(Product, id=product_id, item_state=1)
        if product in user.product_wish_list.all():
            user.product_wish_list.remove(product)
            wish_list = product.wish_lists.count()
            return Response(
                {"wish_list": wish_list}, status=status.HTTP_200_OK
            )
        else:
            user.product_wish_list.add(product)
            wish_list = product.wish_lists.count()
            return Response(
                {"wish_list": wish_list}, status=status.HTTP_201_CREATED
            )


class ReviewListAPIView(APIView):
    """
    POST : 리뷰 좋아요 등록 및 취소
    """

    def post(self, request, review_id):
        """
        리뷰 좋아요 등록 및 취소
        """

        user = get_object_or_404(User, email=request.user.email)
        review = get_object_or_404(Review, id=review_id)
        if review in user.review_like.all():
            user.review_like.remove(review)
            liking_people = review.review_liking_people.count()
            return Response(
                {"liking_people": liking_people}, status=status.HTTP_200_OK
            )
        else:
            user.review_like.add(review)
            liking_people = review.review_liking_people.count()
            return Response(
                {"liking_people": liking_people}, status=status.HTTP_201_CREATED
            )


class FollowAPIView(APIView):
    """
    POST : 팔로우 등록 및 취소
    """

    def post(self, request, user_id):
        """
        사용자를 팔로우, 언팔로우
        """

        user = get_object_or_404(User, pk=request.user.pk)
        owner = get_object_or_404(User, id=user_id)
        if owner.is_seller is False:
            # 팔로우 대상자가 판매자가 아닌 경우
            return Response(
                {"err": "Unprocessable Entity"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        elif owner == user:
            # 팔로우 대상자가 자기 자신이라면
            return Response(
                {"err": "bad request"}, status=status.HTTP_400_BAD_REQUEST
            )

        if owner in user.follower.all():
            user.follower.remove(owner)
            followings = owner.followings.count()
            return Response(
                {"followings": followings}, status=status.HTTP_200_OK
            )
        else:
            user.follower.add(owner)
            followings = owner.followings.count()
            return Response(
                {"followings": followings}, status=status.HTTP_201_CREATED
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
class PointStatisticView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        # 포인트 총합 계산
        """포인트 종류: 출석(1), 텍스트리뷰(2), 포토리뷰(3), 구매(4), 충전(5), 구독권이용료(6), 결제(7), 정산(8), 환불(9)"""
        day_plus_point = (
            Point.objects.filter(user_id=request.user.id)
                .filter(point_type__in=[1, 2, 3, 4, 5, 8, 9])
                .filter(date=date)
                .aggregate(total=Sum("point"))
        )
        day_minus_point = (
            Point.objects.filter(user_id=request.user.id)
                .filter(point_type__in=[6, 7])
                .filter(date=date)
                .aggregate(total=Sum("point"))
        )
        plus_point = (
            day_plus_point["total"] if day_plus_point["total"] is not None else 0
        )
        minus_point = (
            day_minus_point["total"] if day_minus_point["total"] is not None else 0
        )

        month_plus_point = (
            Point.objects.filter(user_id=request.user.id)
                .filter(point_type__in=[1, 2, 3, 4, 5, 8, 9])
                .filter(date__month=timezone.now().date().month)
                .aggregate(total=Sum("point"))
        )
        month_minus_point = (
            Point.objects.filter(user_id=request.user.id)
                .filter(point_type__in=[6, 7])
                .filter(date__month=timezone.now().date().month)
                .aggregate(total=Sum("point"))
        )
        month_plus = (
            month_plus_point["total"] if month_plus_point["total"] is not None else 0
        )
        month_minus = (
            month_minus_point["total"] if month_minus_point["total"] is not None else 0
        )

        total_point = PointStatisticView.get_total_point(request.user)

        return Response(
            {
                "day_plus": plus_point,
                "day_minus": minus_point,
                "month_plus": month_plus,
                "month_minus": month_minus,
                "total_point": total_point,
            },
            status=status.HTTP_200_OK,
        )

    @classmethod
    def get_total_point(self, user):
        total_plus_point = (
            Point.objects.filter(user_id=user.id)
                .filter(point_type__in=[1, 2, 3, 4, 5, 8, 9])
                .aggregate(total=Sum("point"))
        )

        total_minus_point = (
            Point.objects.filter(user_id=user.id)
                .filter(point_type__in=[6, 7])
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

        return total_point


"""포인트 종류: 출석(1)"""


class PointAttendanceView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PointSerializer

    def post(self, request, *args, **kwargs):
        try:
            attendance_point = get_object_or_404(Point, user=self.request.user, point_type=1,
                                                 date=timezone.now().date())
            return Response({"message": "이미 존재"}, status.HTTP_400_BAD_REQUEST)
        except:
            return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, point_type_id=1, point=100)


"""포인트충전 결제후처리"""


class PointCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        amount = request.data.get('amount')
        payment_type = request.data.get('payment_type')

        try:
            trans = PayTransaction.objects.create_new(
                user=user,
                amount=amount,
                payment_type=payment_type
            )
        except:
            trans = None

        if trans is not None:
            data = {
                "works": True,
                "merchant_id": trans
            }

            return JsonResponse(data)
        else:
            return JsonResponse({}, status=status.HTTP_401_UNAUTHORIZED)


class PointImpAjaxView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        merchant_id = request.data.get('merchant_id')
        imp_id = request.data.get('imp_id')
        amount = request.data.get('amount')

        try:
            trans = PayTransaction.objects.get(
                user=user,
                order_id=merchant_id,
                amount=amount
            )
        except:
            trans = None

        if trans is not None:
            try:
                Point.objects.create(user=user, point_type_id=5, point=trans.amount)

                trans.transaction_id = imp_id
                trans.transaction_status = "paid"
                trans.success = True
                trans.save()

                data = {
                    "works": True
                }
                return JsonResponse(data)
            except:
                return JsonResponse({}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return JsonResponse({}, status=status.HTTP_401_UNAUTHORIZED)


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
            try:
                Point.objects.create(user=request.user, point_type_id=6, point=9900)
                serializer.save(user=request.user,
                                next_payment=timezone.now().date() + timedelta(weeks=4))
                return Response({"message": "성공!"}, status=status.HTTP_200_OK)
            except:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
            subscription.next_payment = timezone.now().date() + timedelta(weeks=4)
            subscription.save()
            return Response({"message": "성공!"}, status.HTTP_200_OK)
