import os, datetime, schedule, time
import django



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weasley.settings')
django.setup()

from .models import Point, Subscribe
from .serializers import PointSerializer
from django.db import transaction
from django.utils import timezone
from django.db.models import F, Sum
from .validated import EmailService
from .models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models import User
from datetime import datetime, timedelta

# 구독 갱신(다음 결제일은 4주 뒤) (포인트 차감)
class SubscribecheckView(APIView):

    def get(self, request):
        current_date = datetime.now()
        one_month_ago = current_date - timedelta(days=30)  # 한 달 전 날짜 계산
        two_days_ago = current_date - timedelta(days=2)  # 이틀 전 날짜 계산
        a_week_ago = current_date - timedelta(days=7)  # 일주일 전

        for i in range(2):
            """
            계정 활성화가 되어있고, 
            마지막 로그인이 한달 전 계정 날짜 생성 하기
            """

            information = {
                "email": f'True_one_month_ago{i}@emai.com',
                "password": "123",
                "nickname": "test",
                "introduction": "계정 활성화가 되어있고, 마지막 로그인이 한달 전 계정: 계정이 비활성화 되어야 함",
                "created_at": one_month_ago,
                "updated_at": one_month_ago,
                "last_login": one_month_ago,
                "is_active": True,
            }
            User.objects.create(**information)

        for i in range(2):
            """
            계정 활성화가 되어있지 않고
            로그인 기록이 없으며 가입일이 2틀 전인 계정 생성
            """

            information = {
                "email": f'False_wo_days_ago{i}@emai.com',
                "password": "123",
                "nickname": "test",
                "introduction": "계정 활성화가 되어있지 않고 로그인 기록이 없으며 가입일이 2틀 전인 계정 : 계정이 삭제 되어야함",
                "created_at": two_days_ago,
                "updated_at": two_days_ago,
            }
            User.objects.create(**information)

        for i in range(2):
            """
            계정 활성화가 되어있고
            로그인 기록이 이틀 전인 사용자
            """

            information = {
                "email": f'True_two_days_ago{i}@emai.com',
                "password": "123",
                "nickname": "test",
                "introduction": "계정 활성화가 되어있고 로그인 기록이 이틀 전인 사용자 : 변경 내용 없어야 함",
                "created_at": two_days_ago,
                "updated_at": two_days_ago,
                "last_login": two_days_ago,
                "is_active": True,
            }
            User.objects.create(**information)

        for i in range(2):
            """
            계정 활성화가 되어 있지 않고
            updated_at이 한달전인 계정 생성하기
            """

            information = {
                "email": f'False_one_month_ago{i}@emai.com',
                "password": "123",
                "nickname": "test",
                "introduction": "계정 활성화가 되어 있지 않고 updated_at이 한달전인 계정 생성하기: 계정이 삭제되어야함",
                "created_at": one_month_ago,
                "updated_at": one_month_ago,
                "last_login": one_month_ago,
            }
            User.objects.create(**information)

        for i in range(2):
            """
            계정 활성화가 되어있고
            일주일전
            """

            information = {
                "email": f'True_a_week_ago_{i}@emai.com',
                "password": "123",
                "nickname": "test",
                "introduction": "계정 활성화가 되어있고,일주일전 로그인 사용자 : 변경 내용 없어야 함",
                "created_at": a_week_ago,
                "updated_at": a_week_ago,
                "last_login": a_week_ago,
                "is_active": True,
            }
            User.objects.create(**information)

        return Response({"msg": "완료"}, status=200)


    def post(self, request):
        # 로그인 및 활성화 기록에 따른 제어
        UserControlSystem.delete_inactive_accounts()
        UserControlSystem.delete_user_data()
        UserControlSystem.account_deactivation()
        UserControlSystem.print_user_information()
        
        # 다음 결제일이 오늘의 날짜 이전인 구독들을 삭제(보안목적)
        Subscribe.objects.filter(next_payment__lt=timezone.now().date(), subscribe=True).delete()
        subscribe_users = Subscribe.objects.filter(next_payment=timezone.now().date(), subscribe=True)
        print(subscribe_users)
        
        for subscribe_user in subscribe_users:
            with transaction.atomic():
                total_plus_point = (
                    Point.objects.filter(user_id=subscribe_user.user.id)
                        .filter(point_type__in=[1, 2, 3, 4, 5])
                        .aggregate(total=Sum("point"))
                )
                print(total_plus_point)
                total_minus_point = (
                    Point.objects.filter(user_id=subscribe_user.user.id)
                        .filter(point_type__in=[6, 7])
                        .aggregate(total=Sum("point"))
                )
                print(total_minus_point)
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
        # print("가입하고서 2일동안 계정 인증을 받지 않았고, 로그인 기록이 없는 유저 데이터 삭제")
        # print("이틀 전 날짜 : ", now)
        for user in objects:
            # print(f'사용자 이름 : {user} ,  마지막 수정일 : {user.updated_at}')
            subject_message = 'Choco The Coo에서 안내 메시지를 보냈습니다.'
            content_message = f'{user.email}님께서 가입하고서 2일 이상 계정 인증 및 로그인 이력이 없어 계정을 삭제 했습니다.'
            # EmailService.message_forwarding(user.email, subject_message, content_message)
            user.delete()

    @classmethod
    def account_deactivation(cls):
        """
        마지막 로그인 기록이 30일 이상 지난 사용자의 계정 비 활성화
        """
        now = timezone.now()
        a_month_ago = now - timezone.timedelta(days=30)
        objects = User.objects.filter(is_active=True, updated_at__lt=a_month_ago)
        # print("마지막 로그인 기록이 30일 이상 지난 사용자의 계정 비 활성화")
        # print("한달전 날짜 : ", a_month_ago)
        for user in objects:
            # print(f'사용자 이름 : {user} ,  마지막 수정일 : {user.updated_at},  마지막 로그인 기록 : {user.last_login}')
            subject_message = 'Choco The Coo에서 안내 메시지를 보냈습니다.'
            content_message = f'{user.email}님, 30일 이상 로그인 이력이 없어 계정을 비 활성화 했습니다.'
            # EmailService.message_forwarding(user.email, subject_message, content_message)
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
        # print("계정이 비 활성화 된지 30일이 지났을 경우 계정 삭제")
        # print("한달 전 날짜 : ", a_month_ago)
        for user in objects:
            # print(f'사용자 이름 : {user} ,  마지막 수정일 : {user.updated_at}')
            subject_message = 'Choco The Coo에서 안내 메시지를 보냈습니다.'
            content_message = f'{user.email}님, 휴면 계정으로 전환된지 90일 만큼 지나 계정을 삭제 했습니다.'
            # EmailService.message_forwarding(user.email, subject_message, content_message)
            user.delete()

    @classmethod
    def print_user_information(cls):
        objects = User.objects.all()
        for user in objects:
            print(user.introduction, user.is_active)

# 매일 자정마다 작업 실행
schedule.every().day.at("00:00").do(SubscribecheckView.post)

# 테스트용 한시간에 한 번씩 확인하기
# schedule.every().hours.at("00:00").do(subscribe_check)

# while True:
#     schedule.run_pending()
#     time.sleep(1)
