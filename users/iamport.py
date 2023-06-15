import requests
import json

from django.conf import settings

# get_access_token: 아임포트 서버에 접근할 수 있는 토큰을 발급
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
            raise ValueError("API 통신 오류")
    else:
        raise ValueError("토큰 오류")


# 결제가 끝나고 결제에 대한 정보를 가져옴
def get_transaction(imp_id, *args, **kwargs):
    access_token = get_access_token()

    if access_token:
        url = "https://api.iamport.kr/payments/" + imp_id
        headers = {
            'Authorization': access_token
        }

        req = requests.get(url, headers=headers)
        res = req.json()
        print(res)

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
        else:
            return None
    else:
        raise ValueError("인증 토큰이 없습니다.")
