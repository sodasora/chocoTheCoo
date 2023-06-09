from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.utils import IntegrityError
from .serializers import (CustomTokenObtainPairSerializer, UserSerializer, DeliverySerializer, ReadUserSerializer,
                          SellerSerializer, PointSerializer, SubscriptionSerializer, GetWishListUserInfo,
                          GetReviewUserListInfo)
from .models import User, Delivery, Seller, Point, Subscribe
from django.contrib.auth.hashers import check_password
from . import validated
from products.models import Product, Review
from .cryption import AESAlgorithm
from django.db.models import Sum
from django.utils import timezone
"""
response 는 간단 명료하게 
백엔드 과정을 예측 하지 못하도록 설정할 것 (보안 유지)
"""

class GetEmailAuthCodeAPIView(APIView):
    """
    이메일 인증코드 발송
     """

    def put(self, request):
        """
        이메일 인증코드 발송 및 DB 저장
        """
        user = get_object_or_404(User, email=request.data['email'])
        auth_code = validated.send_email(user.email)
        user.auth_code = auth_code
        print(auth_code)
        user.save()
        return Response({"msg": "인증 코드를 발송 했습니다."}, status=status.HTTP_200_OK)


class UserAPIView(APIView):
    """
    회원가입, 이메일 인증, 휴면 계정 전환
    """

    def post(self, request):
        """
        회원 가입
        """
        serializer = UserSerializer(data=request.data, context="create")
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': "회원 가입 되었습니다. 계정 인증을 진행해 주세요."}, status=status.HTTP_200_OK)
        else:
            return Response({"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
         회원 가입시 이메일 인증  or 휴면 계정 활성화 신청 응답
         """
        user = get_object_or_404(User, email=request.data['email'])
        if user.auth_code is None:
            return Response({"mrr": "먼저 인증코드를 발급받아주세요."}, status=status.HTTP_400_BAD_REQUEST)
        elif not user.auth_code == request.data['auth_code']:
            return Response({"err": "인증 코드가 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.is_active = True
            user.auth_code = None
            user.save()
            return Response({"msg": "인증 되었습니다."}, status=status.HTTP_200_OK)

    def patch(self, request):
        """
        비밀번호 재 설정(찾기 기능)
        """
        user = get_object_or_404(User, email=request.data['email'])
        if user.auth_code == '':
            return Response({"msg": "먼저 인증코드를 발급받아주세요."}, status=status.HTTP_400_BAD_REQUEST)
        elif not user.auth_code == request.data['auth_code']:
            return Response({"err": "인증 코드가 올바르지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            user.auth_code = None
            user.is_active = True
            user.save()
            return Response({"msg": "비밀번호를 재 설정 했습니다."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    """
     마이페이지 정보 읽기, 회원 정보 수정, 휴면 계정으로 전환
    """

    def get(self, request, user_id):
        """
         마이페이지 정보 읽어오기
         """
        user = get_object_or_404(User, id=user_id)
        serializer = ReadUserSerializer(user)
        total_plus_point = Point.objects.filter(user_id=user.id).filter(point_type_id__in=[1, 2, 3, 4, 5]).aggregate(total=Sum('point'))
        total_minus_point = Point.objects.filter(user_id=user.id).filter(point_type_id=6).aggregate(total=Sum('point'))
        try:
            total_point = total_plus_point['total'] - total_minus_point['total']
        except TypeError:
            total_point = total_plus_point['total'] if total_plus_point['total'] is not None else 0
        new_serializer_data = dict(serializer.data)
        new_serializer_data['total_point'] = total_point
        return Response(new_serializer_data, status=status.HTTP_200_OK)

    def put(self, request, user_id):
        """
         회원 정보 수정 (프로필 이미지, 닉네임, 통관번호, 이메일, 비밀번호)
         """
        user = get_object_or_404(User, id=user_id)
        if request.user != user:
            return Response({"err": "권한이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(user, data=request.data, partial=True, context="update")
        if serializer.is_valid():
            serializer.save()
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
            return Response({'err': '권한이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        deliveries_cnt = Delivery.objects.filter(user=user).count()
        if deliveries_cnt > 4:
            return Response({'err': '배송 정보는 다섯개 까지 등록할 수 있습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        if request.data.get("postal_code") is not None:
            serializer = DeliverySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user)
                return Response({'msg': '배송 정보가 등록되었습니다.'}, status=status.HTTP_200_OK)
            else:
                return Response({"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'msg': '우편 번호 정보가 없습니다.'}, status=status.HTTP_204_NO_CONTENT)


class UpdateDeliveryAPIView(APIView):
    """
     배송 정보 수정 및 삭제
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
            return Response({"msg": "배송 정보가 삭제 되었습니다."}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"err": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)


class SellerAPIView(APIView):
    def post(self, request):
        """
         판매자 정보 저장 및 권한 신청
         """
        try:
            user = get_object_or_404(User, email=request.user.email)
        except AttributeError:
            return Response({'err': "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer = SellerSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user)
                return Response({'msg': "판매자 권한을 성공적으로 신청했습니다. 검증 후에 승인 됩니다."}, status=status.HTTP_200_OK)
            else:
                return Response({"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({"err": "이미 판매자 정보가 있습니다."}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
         판매자 정보 수정
         """
        try:
            user = get_object_or_404(User, email=request.user.email)
        except AttributeError:
            return Response({'err': "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer = SellerSerializer(user.user_seller, data=request.data, partial=True)
        except Seller.DoesNotExist:
            return Response({'err': "수정할 판매자 정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': "판매자 정보를 수정 했습니다."}, status=status.HTTP_200_OK)
        else:
            return Response({"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
         판매자 정보 삭제
         """
        try:
            user = get_object_or_404(User, email=request.user.email)
        except AttributeError:
            return Response({'err': "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user.user_seller.delete()
        except Seller.DoesNotExist:
            return Response({'err': "판매자 정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'msg': "판매자 정보를 삭제 했습니다."}, status=status.HTTP_204_NO_CONTENT)


class SellerPermissionAPIView(APIView):
    """
     판매자 정보 읽기 , 관리자가 판매자 정보 권한 승인 및 삭제
     """

    def get(self, request, user_id):
        """
         판매자 정보 읽기
         """
        user = get_object_or_404(User, id=user_id)
        try:
            serializer = SellerSerializer(user.user_seller)
        except Seller.DoesNotExist:
            return Response({'err': "판매자 정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        print(serializer.data)
        decrypt_result = AESAlgorithm.decrypt_all(**serializer.data)
        return Response(decrypt_result, status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        """
        판매자 권한 승인
        """
        try:
            admin = get_object_or_404(User, email=request.user.email)
        except AttributeError:
            return Response({'err': "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        if not admin.is_admin:
            return Response({'err': "올바른 접근 방법이 아닙니다."}, status=status.HTTP_401_UNAUTHORIZED)
        user = get_object_or_404(User, id=user_id)
        user.is_seller = True
        user.save()
        return Response({'msg': "판매자 권한을 승인했습니다."}, status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, user_id):
        """
         판매자 정보 삭제
         """
        try:
            admin = get_object_or_404(User, email=request.user.email)
        except AttributeError:
            return Response({'err': "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        if not admin.is_admin:
            return Response({'err': "올바른 접근 방법이 아닙니다."}, status=status.HTTP_401_UNAUTHORIZED)
        user = get_object_or_404(User, id=user_id)
        try:
            user.user_seller.delete()
        except Seller.DoesNotExist:
            return Response({'err': "판매자 정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'msg': "판매자 정보를 삭제 했습니다."}, status=status.HTTP_204_NO_CONTENT)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
     로그인 , access token 발급
     """
    serializer_class = CustomTokenObtainPairSerializer
    # def post(self, request, *args, **kwargs):
    #     pass


class WishListAPIView(APIView):
    """
    상품 찜 등록한 유저 정보 불러오기,
    상품 찜 등록 및 취소
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
            return Response({"message": "상품 찜 등록을 취소 했습니다."}, status=status.HTTP_204_NO_CONTENT)
        else:
            user.product_wish_list.add(product)
            return Response({"message": "상품을 찜 등록 했습니다."}, status=status.HTTP_201_CREATED)


class ReviewListAPIView(APIView):
    """
    리뷰 좋아요 등록한 유저 정보 불러오기,
    리뷰 좋아요 등록 및 취소
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
            return Response({"message": "리뷰 좋아요를 취소 했습니다."}, status=status.HTTP_204_NO_CONTENT)
        else:
            user.review_like.add(review)
            return Response({"message": "리뷰 좋아요를 등록 했습니다."}, status=status.HTTP_201_CREATED)


"""포인트"""
class PointView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 포인트 적립
        serializer  = PointSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self, request, date):
        # 포인트 상세보기
        points = Point.objects.filter(date=date, user=request.user)
        serializer = PointSerializer(points, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PointDateView(APIView):
    permission_classes = [IsAuthenticated]    
    # 요약보기
    def get(self, request, date):
        # 포인트 총합 계산
        """포인트 종류: 출석(1), 텍스트리뷰(2), 포토리뷰(3), 구매(4), 충전(5), 사용(6)"""
        day_plus_point = Point.objects.filter(user_id=request.user.id).filter(point_type_id__in=[1, 2, 3, 4, 5]).filter(date=date).aggregate(total=Sum('point'))
        day_minus_point = Point.objects.filter(user_id=request.user.id).filter(point_type_id=6).filter(date=date).aggregate(total=Sum('point'))
        month_plus_point = Point.objects.filter(user_id=request.user.id).filter(point_type_id__in=[1, 2, 3, 4, 5]).filter(date__month=timezone.now().date().month).aggregate(total=Sum('point'))
        month_minus_point = Point.objects.filter(user_id=request.user.id).filter(point_type_id=6).filter(date__month=timezone.now().date().month).aggregate(total=Sum('point'))
        total_plus_point =  Point.objects.filter(user_id=request.user.id).filter(point_type_id__in=[1, 2, 3, 4, 5]).aggregate(total=Sum('point'))
        total_minus_point = Point.objects.filter(user_id=request.user.id).filter(point_type_id=6).aggregate(total=Sum('point'))
        
        return Response({
            "day_plus_point":day_plus_point,
            "day_minus_point":day_minus_point,
            "month_minus_point":month_minus_point,
            "month_plus_point":month_plus_point,
            "total_plus_point":total_plus_point,
            "total_minus_point":total_minus_point,
        }, status=status.HTTP_200_OK)


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    # 구독 정보 가져오기
    def get(self, request):
        subscription = get_object_or_404(Subscribe, user_id=request.user.id)
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 구독 최초 생성
    def post(self, request):
        serializer = SubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
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
            subscription.save()
            return Response({"message": "성공!"}, status.HTTP_200_OK)
