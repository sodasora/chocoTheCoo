import datetime, time
from .models import Point, Subscribe
from .serializers import PointSerializer
from django.db import transaction
from django.utils import timezone
from django.db.models import F, Sum
from .validated import EmailService
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models import User
from chat.models import RoomMessage
from datetime import datetime, timedelta

# 구독 갱신(다음 결제일은 4주 뒤) (포인트 차감)
class SubscribecheckView(APIView):

    def post(self, request):
        # 로그인 및 활성화 기록에 따른 제어
        UserControlSystem.delete_inactive_accounts()
        UserControlSystem.delete_user_data()
        UserControlSystem.account_deactivation()
        
        # 일주일 전 채팅은 지워지도록
        one_week_ago = timezone.now() - timedelta(days=7)
        RoomMessage.objects.filter(created_at__lte = one_week_ago).delete()
        
        # 다음 결제일이 오늘의 날짜 이전인 구독들을 삭제(보안목적)
        Subscribe.objects.filter(next_payment__lt=timezone.now().date(), subscribe=True).delete()
        subscribe_users = Subscribe.objects.filter(next_payment=timezone.now().date(), subscribe=True)
        # print(subscribe_users)
        
        for subscribe_user in subscribe_users:
            with transaction.atomic():
                total_plus_point = (
                    Point.objects.filter(user_id=subscribe_user.user.id)
                        .filter(point_type__in=[1, 2, 3, 4, 5, 8])
                        .aggregate(total=Sum("point"))
                )
                # print(total_plus_point)
                total_minus_point = (
                    Point.objects.filter(user_id=subscribe_user.user.id)
                        .filter(point_type__in=[6, 7])
                        .aggregate(total=Sum("point"))
                )
                # print(total_minus_point)
                try:
                    total_point = total_plus_point["total"] - total_minus_point["total"]
                    print(total_point)
                except TypeError:
                    total_point = (
                        total_plus_point["total"]
                        if total_plus_point["total"] is not None
                        else 0
                    )

                # 구독료 9900원
                if total_point >= 9900:
                    point_data = {"point": 9900}
                    serializer = PointSerializer(data=point_data)
                    if serializer.is_valid():
                        serializer.save(user=subscribe_user.user, point_type_id=6)

                    subscribe_user.subscribe = True
                    subscribe_user.next_payment = F('next_payment') + datetime.timedelta(weeks=4)
                    # 테스트용 (1시간 뒤)
                    # subscribe_user.next_payment = F('next_payment')+datetime.timedelta(hours = 1)
                    subscribe_user.save()
                else:
                    subscribe_user.subscribe = False
                    subscribe_user.save()
                
        return Response({"msg":"완료"}, status=status.HTTP_202_ACCEPTED)


class UserControlSystem:
    """
    사용자 계정 관리 시스템
    1. 가입후 2일간 계정 인증을 받지 않은 사용자 데이터 삭제
    2. 30일간 로그인 기록이 없는 계정 비 활성화
    3. 비 활성화 기간 30일이 지난 계정 삭제
    """


    @classmethod
    def delete_user_data(cls):
        """
        가입하고서 2일동안 계정 인증을 받지 않았고, 로그인 기록이 없는 유저 데이터 삭제
        """

        now = timezone.now()
        two_days_ago = now - timedelta(days=2)
        objects = User.objects.filter(last_login=None, is_active=False, updated_at__lt=two_days_ago)
        for user in objects:
            subject_message = 'Choco The Coo에서 안내 메시지를 보냈습니다.'
            content_message = f'{user.email}님께서 가입하고서 2일 이상 계정 인증 및 로그인 이력이 없어 계정을 삭제 했습니다.'
            EmailService.message_forwarding(user.email, subject_message, content_message)
            user.delete()

    @classmethod
    def account_deactivation(cls):
        """
        마지막 로그인 기록이 30일 이상 지난 사용자의 계정 비 활성화
        """

        now = timezone.now()
        a_month_ago = now - timezone.timedelta(days=30)
        objects = User.objects.filter(is_active=True, updated_at__lt=a_month_ago)
        for user in objects:
            subject_message = 'Choco The Coo에서 안내 메시지를 보냈습니다.'
            content_message = f'{user.email}님, 30일 이상 로그인 이력이 없어 계정을 비 활성화 했습니다.'
            EmailService.message_forwarding(user.email, subject_message, content_message)
            user.is_active = False
            user.save()

    @classmethod
    def delete_inactive_accounts(cls):
        """
        계정이 비 활성화 된지 30일이 지났을 경우 계정 삭제
        """

        now = timezone.now()
        a_month_ago = now - timezone.timedelta(days=30)
        objects = User.objects.filter(is_active=False, updated_at__lt=a_month_ago)
        for user in objects:
            subject_message = 'Choco The Coo에서 안내 메시지를 보냈습니다.'
            content_message = f'{user.email}님, 휴면 계정으로 전환된지 90일 만큼 지나 계정을 삭제 했습니다.'
            EmailService.message_forwarding(user.email, subject_message, content_message)
            user.delete()


# 매일 자정마다 작업 실행
# schedule.every().day.at("00:00").do(SubscribecheckView.post)

# 테스트용 한시간에 한 번씩 확인하기
# schedule.every().hours.at("00:00").do(subscribe_check)

# while True:
#     schedule.run_pending()
#     time.sleep(1)
