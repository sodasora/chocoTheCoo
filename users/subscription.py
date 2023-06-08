from .models import Point, Subscribe
from django.db import transaction
import datetime, schedule, time
from django.utils import timezone
from django.db.models import F

# 구독 갱신(다음 결제일은 4주 뒤) (포인트 차감)
def subscribe_check():
    # 다음 결제일이 오늘의 날짜 이전인 구독들을 삭제(보안목적)
    Subscribe.objects.filter(next_payment__lt=timezone.now().date(), subscribe=True).delete()
    subscribe_users = Subscribe.objects.filter(next_payment=timezone.now().date(), subscribe=True)
    
    for subscribe_user in subscribe_users:
        with transaction.atomic():
            user_point = Point.objects.get(user_id=subscribe_user['user_id'])
            
            # 구독료 9900원
            if user_point >= 9900:
                user_point.points -= 9900
                user_point.save()
                
                subscribe_user.subscribe = True
                subscribe_user.next_payment = F('next_payment')+datetime.timedelta(weeks = 4)
                # 테스트용 (1시간 뒤)
                # subscribe_user.next_payment = F('next_payment')+datetime.timedelta(hours = 1)
                subscribe_user.save()
            else:
                subscribe_user.subscribe = False
                subscribe_user.save()

# 매일 자정마다 작업 실행
schedule.every().day.at("00:00").do(subscribe_check)

# 테스트용 한시간에 한 번씩 확인하기
# schedule.every().hours.at("00:00").do(subscribe_check)

while True:
    schedule.run_pending()
    time.sleep(1)