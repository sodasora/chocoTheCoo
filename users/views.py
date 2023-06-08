import django.db.utils
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (CustomTokenObtainPairSerializer,UserSerializer,DeliverieSerializer,ReadUserSerializer,SellerSerializer, PointSerializer, SubscriptionSerializer)
from .models import User,Deliverie,Seller, Point, Subscribe
from django.contrib.auth.hashers import check_password
from . import validated
from django.db.models import Sum

class GetEmailAuthCode(APIView):
    """ 이메일 인증코드 발송 """
    def put(self, request):
        """ 이메일 인증코드 발송 및 DB 저장 """
        user = get_object_or_404(User, email=request.data['email'])
        auth_code = validated.send_email(user.email)
        user.auth_code = auth_code
        user.save()
        return Response({"msg": "인증 코드를 발송 했습니다."}, status=status.HTTP_400_BAD_REQUEST)

class UserAPIView(APIView):
    """ 회원가입, 회원 정보 수정, 휴면 계정 전환"""
    def get(self,request):
        """ 테스트옹 API, 유저 정보 읽기 """

        user = get_object_or_404(User,email=request.data.get("email"))
        serializer = ReadUserSerializer(user)
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self,request):
        """ 회원 가입 """
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': "회원 가입 되었습니다. 계정 인증을 진행해 주세요."}, status=status.HTTP_200_OK)
        else:
            return Response({"err":serializer.errors},status=status.HTTP_400_BAD_REQUEST)

    def put(self,request):
        """ 회원 가입시 이메일 인증  or 휴면 계정 활성화 신청 응답 """
        user = get_object_or_404(User, email=request.data['email'])
        if user.auth_code == None:
            return Response({"mrr":"먼저 인증코드를 발급받아주세요."},status=status.HTTP_400_BAD_REQUEST)
        elif not user.auth_code == request.data['auth_code']:
            return Response({"err":"인증 코드가 올바르지 않습니다."},status=status.HTTP_400_BAD_REQUEST)
        else:
            user.is_active = True
            user.auth_code = None
            user.save()
            return Response({"msg": "인증 되었습니다."}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self,request):
        """ 비밀번호 재 설정(찾기 기능) """
        user = get_object_or_404(User,email = request.data['email'])
        if check_password(request.data['password'], user.password):
            return Response({"msg": "기존의 비밀번호로 변경할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        if user.auth_code == '':
            return Response({"msg":"먼저 인증코드를 발급받아주세요."},status=status.HTTP_400_BAD_REQUEST)
        elif not user.auth_code == request.data['auth_code']:
            return Response({"err":"인증 코드가 올바르지 않습니다."},status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            user.auth_code = None
            user.is_active = True
            user.save()
            return Response({"msg":"비밀번호를 재 설정 했습니다."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeliverieAPIView(APIView):
    """ 배송 정보 추가 """
    def get(self,request,user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = DeliverieSerializer(user.deliveries_data,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request,user_id):
        user = get_object_or_404(User, id=user_id)
        deliverie_cnt = Deliverie.objects.filter(user=user).count()
        if deliverie_cnt > 4:
            return Response({'err': '배송 정보는 다섯개 까지 등록할 수 있습니다.'}, status=status.HTTP_200_OK)
        if request.data.get("postal_code") != None:
            serializer = DeliverieSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user)
                return Response({'msg': '배송 정보가 등록되었습니다.'}, status=status.HTTP_200_OK)
            else:
                return Response({"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        # 회원가입시 필수 입력 사항이 아니기 때문에 status code 를 204 사용
        return Response({'msg': '우편 번호 정보가 없습니다.'}, status=status.HTTP_204_NO_CONTENT)

class UpdateDeliverieAPIView(APIView):
    """ 배송 정보 수정 및 삭제 """
    def put(self,request,deliverie_id):
        """ 배송 정보 수정 """
        deliverie = get_object_or_404(Deliverie, id=deliverie_id)
        if request.user == deliverie.user:
            serializer = DeliverieSerializer(deliverie, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"err":"권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, deliverie_id):
        """ 배송 정보가 삭제 되었습니다."""
        deliverie = get_object_or_404(Deliverie, id=deliverie_id)
        if request.user == deliverie.user:
            deliverie.delete()
            return Response({"msg": "배송 정보가 삭제 되었습니다."}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"err": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

class SellerAPIView(APIView):
    def post(self,request):
        """ 판매자 정보 저장 및 권한 신청 """
        try:
            user = get_object_or_404(User,email=request.user.email)
        except AttributeError:
            return Response({'err': "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer = SellerSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user)
                return Response({'msg': "판매자 권한을 성공적으로 신청했습니다. 검증 후에 승인 됩니다."}, status=status.HTTP_200_OK)
            else:
                return Response({"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except django.db.utils.IntegrityError:
            return Response({"err": "이미 판매자 정보가 있습니다."}, status=status.HTTP_400_BAD_REQUEST)

    def put(self,request):
        """ 판매자 정보 수정 """
        try:
            user = get_object_or_404(User,email=request.user.email)
        except AttributeError:
            return Response({'err': "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = SellerSerializer(user.user_seller,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': "판매자 정보를 수정 했습니다."}, status=status.HTTP_200_OK)
        else:
            return Response({"err": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request):
        """ 판매자 정보 삭제 """
        try:
            user = get_object_or_404(User,email=request.user.email)
        except AttributeError:
            return Response({'err': "로그인이 필요 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user.user_seller.delete()
        except Seller.DoesNotExist:
            return Response({'err': "판매자 정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'msg': "판매자 정보를 삭제 했습니다."}, status=status.HTTP_204_NO_CONTENT)

class SellerPermissionAPIView(APIView):
    """ 관리자가 판매자 정보 권한 승인 및 삭제 """
    def patch(self,request,user_id):
        """ 판매자 권한 승인 """
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

    def delete(self,request,user_id):
        """ 판매자 정보 삭제 """
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
    """ 로그인 , access token 발급 """
    serializer_class = CustomTokenObtainPairSerializer


"""포인트"""
class PointView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer  = PointSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PointDateView(APIView):
    permission_classes = [IsAuthenticated]    
    # 날짜별 상세보기
    def get(self, request, date):
        # 포인트 총합 계산
        """포인트 종류: 출석(1), 리뷰(2), 구매(3), 충전(4), 사용(5)"""
        total_plus_point = Point.objects.filter(user_id=request.user.id).filter(point_type_id=1|2|3|4).filter(date=date).aggregate(total=Sum('points'))
        total_minus_point = Point.objects.filter(user_id=request.user.id).filter(point_type_id=5).filter(date=date).aggregate(total=Sum('points'))
        total_point = total_plus_point - total_minus_point
        
        # 포인트 상세보기
        points = Point.objects.filter(date=date, user=request.user)
        
        return Response({
            "total_plus_point":total_plus_point,
            "total_minus_point":total_minus_point,
            "total_point":total_point,
            "points": points
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
    def patch(self,request):
        subscription = get_object_or_404(Subscribe, user_id=request.user.id)
        if subscription.subscribe == True:
            subscription.subscribe = False
            subscription.save()
            return Response({"message": "해지"}, status.HTTP_200_OK)
        else:
            subscription.subscribe = True
            subscription.save()
            return Response({"message": "성공!"}, status.HTTP_200_OK)
        