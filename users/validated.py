from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.hashers import check_password
import random, re, string, json
import hashlib, hmac, base64, os, requests, time
from django.utils import timezone
from datetime import timedelta
from .models import EmailVerification,PhoneVerification,Delivery

NAVER_SMS_ACCESS_KEY = os.environ.get('NAVER_SMS_ACCESS_KEY')
NAVER_SMS_SECRET_KEY = os.environ.get('NAVER_SMS_SECRET_KEY')
NAVER_SMS_PROJECT_ID = os.environ.get('NAVER_SMS_PROJECT_ID')

SENDING_URI = f'https://sens.apigw.ntruss.com/sms/v2/services/{NAVER_SMS_PROJECT_ID}/messages'
URL = "https://sens.apigw.ntruss.com"
URI = f'/sms/v2/services/{NAVER_SMS_PROJECT_ID}/messages'
CALLING_NUMBER = os.environ.get('CALLING_NUMBER')


class SmsSendView(APIView):
    """
    네이버 문자 발송 받기
    """

    @classmethod
    def get_auth_numbers(cls):
        """
        4자리 숫자의 인증 번호 반환
        """
        result = "".join([str(random.randint(0, 9)) for _ in range(4)])
        return result

    @classmethod
    def make_signature(cls, timestamp):
        """
        네이버 클라우드 클랫폼 시그니쳐 생성
        # https://api.ncloud-docs.com/docs/common-ncpapi
        # HMAC 암호화 알고리즘은 HmacSHA256 사용
        """
        access_key = NAVER_SMS_ACCESS_KEY
        secret_key = NAVER_SMS_SECRET_KEY
        secret_key = bytes(secret_key, 'UTF-8')
        method = "POST"
        uri = URI
        message = method + " " + uri + "\n" + timestamp + "\n" + access_key
        message = bytes(message, 'UTF-8')
        signing_key = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest())
        return signing_key

    @classmethod
    def send_sms(cls, phone_number, content):
        """
        메시지 발송
        request
         - phone_number : '-'를 제외한 숫자만 입력
         - content : 80byte 를 넘지 않는 길이
        """
        timestamp = str(int(time.time() * 1000))
        header = {
            "Content-Type": "application/json; charset=utf-8",
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-iam-access-key": NAVER_SMS_ACCESS_KEY,
            "x-ncp-apigw-signature-v2": cls.make_signature(timestamp),
        }
        body = {
            "type": "SMS",
            "contentType": "COMM",
            "countryCode": "82",
            "from": '01031571180',
            "content": content,
            "messages": [
                {
                    "to": phone_number,
                }
            ]
        }

        requests.post(
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
    def set_information(cls,subject_message,content_message):
        information = {
            'subject_message': subject_message,
            'content_message': content_message,
        }
        return information

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
    def message_forwarding(cls, email, subject_message, content_message):
        """
        이메일 발송
        """

        title = "Choco The Coo"
        context = cls.set_information(subject_message, content_message)
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

    def validated_postal_code(cls,**kwargs):
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

    @classmethod
    def validated_phone_number(cls,numbers):
        """
        핸드폰 번호 검증
        """
        check = [
            lambda element: element != None,
            # None값이 아니라면 True
            lambda element: len(element) == len(element.replace(" ", "")),
            # 공백이 포함 되어 있을 경우 False
            lambda element: len(element) == 11,
            # 11자리가 아니라면 False
            lambda element: element.isdigit()
            # 숫자가 아닌 값이 들어 있다면 False
        ]
        for i in check:
            if not i(numbers):
                return False
        return True


    @classmethod
    def validated_email_verification_code(cls, user,request_verification_code):
        """
        이메일 인증 코드 유효성 검사
        """

        if user.login_type != "normal":
            # 소셜 로그인일 경우 이메일 인증이 필요 없음을 알림
            return status.HTTP_403_FORBIDDEN
        try:
            # 사용자에게 등록된 이메일 인증번호 불러오기
            verification_code = user.email_verification.verification_code
        except EmailVerification.DoesNotExist:
            # 원투원 필드가 없을 경우 예외처리
            return status.HTTP_406_NOT_ACCEPTABLE

        if verification_code is None:
            # 인증 코드를 발급받지 않았을 경우 예외 처리
            return status.HTTP_406_NOT_ACCEPTABLE
        elif not (timezone.now() - user.email_verification.updated_at) <= timedelta(minutes=5):
            user.email_verification.verification_code = None
            user.email_verification.save()
            # 인증 유효 기간이 지났을 경우 예외 처리
            return status.HTTP_408_REQUEST_TIMEOUT
        elif not verification_code == request_verification_code:
            # 사용자가 입력한 이메일 인증번호와, 등록된 이메일 인증번호가 일치하지 않을 경우 예외처리
            return status.HTTP_409_CONFLICT
        else:
            return True

    @classmethod
    def validated_phone_verification(cls, user, request_verification_numbers):
        """
        휴대폰 인증 코드 유효성 검사
        """

        try:
            # 사용자에게 등록된 휴대폰 인증 번호 불러오기
            verification_numbers = user.phone_verification.verification_numbers
        except PhoneVerification.DoesNotExist:
            # 원투원 필드가 없을 경우 예외처리
            return status.HTTP_406_NOT_ACCEPTABLE

        if verification_numbers is None:
            # 인증 코드를 발급받지 않았을 경우 예외 처리
            return status.HTTP_406_NOT_ACCEPTABLE
        elif not (timezone.now() - user.phone_verification.updated_at) <= timedelta(minutes=5):
            user.phone_verification.verification_code = None
            user.phone_verification.save()
            # 인증 유효 기간이 지났을 경우 예외 처리
            return status.HTTP_408_REQUEST_TIMEOUT
        elif not verification_numbers == request_verification_numbers:
            # 사용자가 입력한 이메일 인증번호와, 등록된 이메일 인증번호가 일치하지 않을 경우 예외처리
            return status.HTTP_409_CONFLICT
        else:
            return True

    @classmethod
    def validated_updated_user_information(cls,user,request):
        """
        회원 정보 수정 접근 유효성 검사
        """

        if request.user != user:
            # 로그인을 하지 않았거나 올바르지 않은 경로로 접근
            return status.HTTP_401_UNAUTHORIZED
        elif user.login_type != "normal" and request.data.get('password') is not None and request.data.get('eamil') is not None:
            # 소셜 로그인 계정이 이메일 또는 비밀번호를 변경 하고자 하는 경우
            return status.HTTP_403_FORBIDDEN
        elif request.data.get('password') or request.data.get('new_password'):
            # 비밀 번호를 변경 하고자 할때 변경
            if not (request.data.get('password') is not None and request.data.get('new_password') is not None):
                #둘중 하나의 값이 빈 값일 경우
                return status.HTTP_422_UNPROCESSABLE_ENTITY
            elif not check_password(request.data.get('password'), user.password):
                return status.HTTP_409_CONFLICT

        return True

    @classmethod
    def validated_deliveries(cls, user,request):
        """
        배송 정보 작성 유효성 검사
        """
        deliveries_cnt = Delivery.objects.filter(user=user).count()
        try:
            if request.user != user:
                # 로그인이 필요하거나 올바르지 않은 접근 방법
                return status.HTTP_401_UNAUTHORIZED
            elif user.phone_verification.is_verified is False:
                # 핸드폰 인증을 받지 않았을 경우
                return status.HTTP_402_PAYMENT_REQUIRED
            elif deliveries_cnt > 4:
                # 배송 정보를 다섯개 이상 등록 했을 경우
                return status.HTTP_400_BAD_REQUEST
            elif request.data.get("postal_code") is None:
                # 우편 번호를 작성하지 않았을 경우
                return status.HTTP_422_UNPROCESSABLE_ENTITY
            else:
                return True
        except PhoneVerification.DoesNotExist:
            # 핸드폰 번호를 등록하지 않았을 경우
            return status.HTTP_402_PAYMENT_REQUIRED
