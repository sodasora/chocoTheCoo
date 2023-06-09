import requests
import json

from django.conf import settings

# get_access_token: 아임포트 서버에 접근할 수 있는 토큰을 발급
# 토큰으로 유저가 결제한 정보를 가져옴
def get_access_token():
    access_data = {
        'imp_key': settings.IAMPORT_KEY,
        'imp_secret': settings.IAMPORT_SECRET
    }

    url = "https://api.iamport.kr/users/getToken"
    req = requests.post(url, data=access_data)
    access_res = req.json()

    if access_res['code'] == 0:
        return access_res['response']['access_token']
    else:
        return None


# 결제를 검증하는 단계
def validation_prepare(merchant_id, amount, *args, **kwargs):
    access_token = get_access_token()

    if access_token:
        access_data = {
            'merchant_uid': merchant_id,
            'amount': amount
        }

        url = "https://api.iamport.kr/payments/prepare"

        headers = {
            'Authorization': access_token
        }

        req = requests.post(url, data=access_data, headers=headers)
        res = req.json()

        if res['code'] != 0:
            raise ValueError("API 연결에 문제가 생겼습니다.")
    else:
        raise ValueError("인증 토큰이 없습니다.")


# 결제가 끝나고 결제에 대한 정보를 가져옴
def get_transaction(merchant_id, *args, **kwargs):
    access_token = get_access_token()

    if access_token:
        # 맞는 url인지 검증해보기
        url = "https://api.iamport.kr/payments/find/" + merchant_id

        headers = {
            'Authorization': access_token
        }

        req = requests.post(url, headers=headers)
        res = req.json()

        if res['code'] == 0:
            context = {
                'imp_id': res['response']['imp_uid'],
                'merchant_id': res['response']['merchant_uid'],
                'amount': res['response']['amount'],
                'status': res['response']['status'],
                'type': res['response']['pay_method'],
                'receipt_url': res['response']['receipt_url']
            }
            return context
        # 결제테이블에 orm을 이용해서 하나씩 값을 저장 save 메소드 이용해서 하기 (유저id도 포함) -> front에서 메세지, statuscode 넘겨주기 
        # 카카오 알림톡 모듈이나 이메일 연결해서 알림톡보내주기 
        else:
            return None
    else:
        raise ValueError("인증 토큰이 없습니다.")
