from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.views import APIView
from django.contrib.auth.hashers import check_password
import random, re, string, json
import hashlib, hmac, base64, os, requests, time
from django.utils import timezone
from datetime import timedelta

import users.models

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
        context = {
            'subject_message': subject_message,
            'content_message': content_message,
        }
        content = render_to_string('email_template.html', context)

        mail = EmailMessage(title, content, to=[email])
        mail.content_subtype = "html"
        mail.send()

    @classmethod
    def send_email_verification_code(cls, user, email, mod):
        if user.login_type != 'normal':
            # 소셜 계정으로 가입된 사용자일 경우 예외 처리
            return [False, '소셜 계정으로 가입된 이메일 입니다.']
        elif ValidatedData.validated_email(email) is not True:
            return [False, '이메일 형식이 올바르지 않습니다.']

        verification_code = cls.get_authentication_code()
        try:
            # 원투원 필드가 존재하면 인증 코드만 수집
            email_verification = user.email_verification
            email_verification.verification_code = verification_code
        except users.models.EmailVerification.DoesNotExist:
            # 원투원 필드가 존재하지 않으면 원투원 필드 생성
            email_verification = users.models.EmailVerification(user=user, verification_code=verification_code)
        email_verification.authentication_type = mod
        email_verification.save()

        subject_message = 'Choco The Coo has sent a verification email'
        content_message = verification_code
        EmailService.message_forwarding(email, subject_message, content_message)
        return True


class ValidatedData:
    """
    데이터 검증 클래스
    """

    @classmethod
    def validated_password(cls, password):
        """
        비밀 번호 검증
        """

        check = [
            lambda element: all(
                x.isdigit() or x.islower() or x.isupper() or (x in ['!', '@', '#', '$', '%', '^', '&', '*', '_']) for x
                in element),
            # 요소 하나 하나를 순환하며 숫자,소문자,대문자,지정된 특수문자 제외한 요소가 있을경우 False
            lambda element: any(x in ['!', '@', '#', '$', '%', '^', '&', '*', '_'] for x in element),
            # 최소 하나 이상의 특수문자 요구
            lambda element: any(x.isdigit() for x in element),
            # 최소 하나 이상의 숫자 요구
            lambda element: len(element) == len(element.replace(" ", "")),
            # 공백이 포함 되어 있을 경우 False
            lambda element: True if (len(element) > 5 and len(element) < 21) else False,
            # 전달된 값의 개수가 5~20 사이일 경우 True
            lambda element: any(x.islower() or x.isupper() for x in element),
            # 요소 하나하나를 순환하며, 요소중 대문자 또는 소문자가 있어야함(숫자로만 가입 불가능)
        ]
        for i in check:
            if not i(password):
                return False
        return True

    @classmethod
    def validated_nickname(cls, nickname):
        """
        닉네임 검증
        """

        check = [
            lambda element: element is not None,
            lambda element: len(element) == len(element.replace(" ", "")),
            lambda element: True if (1 < len(element) < 20) else False,
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
        이메일,닉네임,비밀 번호 검증
        """

        if not cls.validated_email(kwargs.get('email')):
            return [False, '이메일 정보가 올바르지 않습니다.']
        elif not cls.validated_nickname(kwargs.get('nickname')):
            return [False, '닉네임 정보가 올바르지 않습니다.']
        elif not cls.validated_password(kwargs.get('password')):
            return [False, '비밀번호가 올바르지 않습니다.']
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
                return [False, '이메일 정보가 올바르지 않습니다.']
        if nickname is not None:
            if not cls.validated_nickname(nickname):
                return [False, '닉네임 정보가 올바르지 않습니다.']
        if password is not None:
            if not cls.validated_password(password):
                return [False, '비밀번호가 올바르지 않습니다.']
        if customs_code is not None:
            if not cls.validated_customs_code(customs_code):
                return [False, '통관번호 정보가 올바르지 않습니다.']
        return True

    @classmethod
    def validated_postal_code(cls, postal_code):
        """
        우편 번호 양식 : https://www.epost.go.kr/search/zipcode/cmzcd003k01.jsp
        """

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
    def address_information_verification(cls, **information):
        """
        배송 정보 검증
        상세 주소를 제외한 데이터가 값이 없거나 공백으로만 기록 되었는지 확인
        """

        check_list = [
            information.get('address'),
            information.get('recipient'),
        ]

        try:
            return all([False if len(element.replace(" ", "")) == 0 else True for element in check_list])
        except AttributeError:
            return False

    @classmethod
    def validated_phone_number(cls, numbers):
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
    def validated_email_verification_code(cls, user, request_verification_code, mod):
        """
        이메일 인증 코드 유효성 검사
        """

        if user.login_type != "normal":
            # 소셜 로그인일 경우 이메일 인증이 필요 없음을 알림
            return [False, '소셜 로그인 계정 입니다.']
        try:
            # 사용자에게 등록된 이메일 인증번호 불러오기
            verification_code = user.email_verification.verification_code
        except users.models.EmailVerification.DoesNotExist:
            # 원투원 필드가 없을 경우 예외처리
            return [False, '인증 코드를 발급 받아 주세요.']

        if verification_code is None:
            # 인증 코드를 발급받지 않았을 경우 예외 처리
            return [False, '인증 코드를 발급 받아 주세요.']
        elif user.email_verification.authentication_type != mod:
            # 발급 받은 유형의 인증 코드를 다른 용도로 사용할 경우
            return [False, '현재 발급 받은 인증 코드 유형이 올바르지 않습니다.']
        elif not (timezone.now() - user.email_verification.updated_at) <= timedelta(minutes=5):
            # 인증 유효 기간이 지났을 경우 예외 처리
            user.email_verification.verification_code = None
            user.email_verification.save()
            return [False, '인증 코드 유효 기간이 만료되었습니다.']
        elif not verification_code == request_verification_code:
            # 사용자가 입력한 이메일 인증번호와, 등록된 이메일 인증번호가 일치하지 않을 경우 예외처리
            return [False, '인증 코드가 일치하지 않습니다.']
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
        except users.models.PhoneVerification.DoesNotExist:
            # 원투원 필드가 없을 경우 예외처리
            return [False, '핸드폰 정보를 등록해 주세요.']

        if verification_numbers is None:
            # 인증 코드를 발급받지 않았을 경우 예외 처리
            return [False, '인증 번호를 발급받아 주세요.']
        elif not (timezone.now() - user.phone_verification.updated_at) <= timedelta(minutes=5):
            user.phone_verification.verification_code = None
            user.phone_verification.save()
            # 인증 유효 기간이 지났을 경우 예외 처리
            return [False, '인증 번호 유효기간이 만료되었습니다.']
        elif not verification_numbers == request_verification_numbers:
            # 사용자가 입력한 이메일 인증번호와, 등록된 이메일 인증번호가 일치하지 않을 경우 예외처리
            return [False, '인증 번호가 일치하지 않습니다.']
        else:
            return True

    @classmethod
    def validated_deliveries(cls, user, request):
        """
        배송 정보 작성 유효성 검사
        """

        deliveries_cnt = users.models.Delivery.objects.filter(user=user).count()
        try:
            if user.phone_verification.is_verified is False:
                # 핸드폰 인증을 받지 않았을 경우
                return [False, '핸드폰 인증이 필요합니다.']
            elif deliveries_cnt > 4:
                # 배송 정보를 다섯개 이상 등록 했을 경우
                return [False, '배송 정보를 다섯개 이상 등록 하셨습니다.']
            elif cls.validated_postal_code(request.get("postal_code")) is not True:
                # 우편 번호를 작성하지 않았을 경우
                return [False, '우편 번호가 올바르지 않습니다.']
            elif cls.address_information_verification(**request) is not True:
                # 상세 정보, 수령인 데이터 검증
                return [False, '주소지 정보가 올바르지 않습니다.']
            else:
                return True
        except users.models.PhoneVerification.DoesNotExist:
            # 핸드폰 번호를 등록하지 않았을 경우
            return [False, '핸드폰 인증이 필요합니다.']

    @classmethod
    def user_password_update_validation(cls, instance, attrs):
        """
        비밀 번호 수정 유효성 검사
        """

        password = attrs.get('password')
        new_password = attrs.get('new_password')
        if instance.login_type != "normal":
            return [False, '소셜 계정으로 가입된 사용자 입니다.']
        elif not check_password(password, instance.password):
            return [False, '입력하신 비밀번호가 사용자의 비밀번호와 일치하지 않습니다.']
        elif not cls.validated_password(new_password):
            return [False, '비밀번호는 영문자,숫자,특수문자로 길이 5이상의 조건이 충족되어야 합니다.']
        else:
            return True
