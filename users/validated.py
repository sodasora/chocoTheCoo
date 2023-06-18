import random, re, string,json
import hashlib, hmac, base64, os, requests, time
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.views import APIView

NAVER_SMS_ACCESS_KEY = os.environ.get('NAVER_SMS_ACCESS_KEY')
NAVER_SMS_SECRET_KEY = os.environ.get('NAVER_SMS_SECRET_KEY')
NAVER_SMS_PROJECT_ID = os.environ.get('NAVER_SMS_PROJECT_ID')

SENDING_URI = f'https://sens.apigw.ntruss.com/sms/v2/services/{NAVER_SMS_PROJECT_ID}/messages'
URL = "https://sens.apigw.ntruss.com"
URI = f'/sms/v2/services/{NAVER_SMS_PROJECT_ID}/messages'
CALLING_NUMBER = os.environ.get('CALLING_NUMBER')


def	make_signature(timestamp):
    access_key = NAVER_SMS_ACCESS_KEY
    secret_key = NAVER_SMS_SECRET_KEY
    secret_key = bytes(secret_key, 'UTF-8')
    method = "POST"
    uri = URI
    message = method + " " + uri + "\n" + timestamp + "\n" + access_key
    message = bytes(message, 'UTF-8')
    signingKey = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest())
    return signingKey


# 네이버 SMS 인증
class SmsSendView(APIView):
    def send_sms(self, phone_number):
        timestamp = str(int(time.time() * 1000))
        header = {
            "Content-Type": "application/json; charset=utf-8",
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-iam-access-key": NAVER_SMS_ACCESS_KEY,
            "x-ncp-apigw-signature-v2": make_signature(timestamp),
        }
        body = {
            "type": "SMS",
            "contentType": "COMM",
            "countryCode": "82",
            "from": '01031571180',
            "content": "내용",
            "messages": [
                {
                    "to": '01031571180',
                }
            ]
        }

        api_result = requests.post(
            SENDING_URI,
            headers=header,
            data=json.dumps(body)
        )
        


class EmailService:
    """
    이메일 발송 및 인증코드 만들기
    템플릿 경로 : .users/templates/email_template.html
    """

    @classmethod
    def get_authentication_code(cls):
        """
        랜덤 값 반환
        """

        random_value = string.ascii_letters + string.digits
        random_value = list(random_value)
        random.shuffle(random_value)
        code = "".join(random_value[:10])
        return code

    @classmethod
    def message_forwarding(cls, **information):
        """
        이메일 발송
        """

        title = "Choco The Coo"

        email = information.get('email')
        context = information.get('context')

        content = render_to_string('email_template.html', context)

        mail = EmailMessage(title, content, to=[email])
        mail.content_subtype = "html"
        mail.send()


class ValidatedData:
    """
    데이터 검증 클래스
    https://github.com/sungsu05/B2Coin_algorithm/blob/master/05_30/SonSungSu/validate_test.py
    """

    @classmethod
    def validated_password(cls, password):
        """
        비밀 번호 검증
        """

        if password is None:
            return False
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        password_match = re.match(password_pattern, password)
        return bool(password_match)

    @classmethod
    def validated_nickname(cls, nickname):
        """
        유저 네임 검증
        """

        check = [
            lambda element: element is not None,
            lambda element: len(element) == len(element.replace(" ", "")),
            lambda element: True if (1 < len(element) < 10) else False,
        ]
        for i in check:
            if not i(nickname):
                return False
        return True

    @classmethod
    def validated_email(cls, email):
        """
        이메일 검증
        """

        if email is None:
            return False
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        email_match = re.match(email_pattern, email)
        return bool(email_match)

    @classmethod
    def validated_customs_code(cls, customs_clearance_number):
        """
        통관 번호 검증
        """

        number = customs_clearance_number.lower()
        check = [
            lambda element: element is not None,
            lambda element: len(element) == len(element.replace(" ", "")),
            lambda element: True if (10 < len(element) < 13) else False,
            lambda element: element[1:].isdigit()
        ]
        for i in check:
            if not i(number):
                return False
        return True

    @classmethod
    def validated_user_data(cls, **kwargs):
        """
        회원 가입용
        이메일,유저 네임,비밀 번호 검증
        """

        if not cls.validated_email(kwargs.get('email')):
            return False
        elif not cls.validated_nickname(kwargs.get('nickname')):
            return False
        elif not cls.validated_password(kwargs.get('password')):
            return False
        return True

    @classmethod
    def update_validated_user_data(cls, **kwargs):
        """
        회원 정보 수정용
        이메일,유저 네임,비밀번호 검증
        """

        email = kwargs.get('email')
        nickname = kwargs.get('nickname')
        password = kwargs.get('password')
        customs_code = kwargs.get('customs_code')
        if email is not None:
            if not cls.validated_email(email):
                return False
        if nickname is not None:
            if not cls.validated_nickname(nickname):
                return False
        if password is not None:
            if not cls.validated_password(password):
                return False
        if customs_code is not None:
            if not cls.validated_customs_code(customs_code):
                return False
        return True

    @classmethod
    def validated_deliveries(cls, **kwargs):
        """
        우편 번호 양식 : https://www.epost.go.kr/search/zipcode/cmzcd003k01.jsp
        """

        postal_code = kwargs.get('postal_code')
        check = [
            lambda element: element is not None,
            lambda element: len(element) == len(element.replace(" ", "")),
            lambda element: True if len(element) == 5 else False,
            lambda element: element.isdigit(),
        ]
        for i in check:
            if not i(postal_code):
                return False
        return True
