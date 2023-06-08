import random, re, string
from django.core.mail import EmailMessage


def send_email(email):
    """ 인증 메일 발송 """
    random_value = string.ascii_letters + string.digits
    random_value = list(random_value)
    random.shuffle(random_value)
    code = "".join(random_value[:10])
    title = "ChocoTheCoo"
    content = "초코더쿠에서 회원님의 가입 인증을 위한 코드를 발송했습니다.\n"
    content += "스파르타 코딩클럽 학생들의 팀 프로젝트이니 혹여 요쳥하신적이 없다면 무시해주세요.\n"
    content += "요청하신분이 맞다면, 아래의 인중코드를 인증란에 작성해주십시오.\n"
    content += code
    mail = EmailMessage(title, content, to=[email])
    mail.send()
    return code


class ValidatedData:
    """ 데이터 검증 클래스 """

    # 데이터 검증 클래스 설명 https://github.com/sungsu05/B2Coin_algorithm/blob/master/05_30/SonSungSu/test2.py
    @classmethod
    def validated_password(cls, password):
        """ 비밀 번호 검증 """
        if password is None:
            return False
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        password_match = re.match(password_pattern, password)
        return bool(password_match)

    @classmethod
    def validated_nickname(cls, nickname):
        """ 유저 네임 검증 """
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
        """ 이메일 검증"""
        if email is None:
            return False
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        email_match = re.match(email_pattern, email)
        return bool(email_match)

    @classmethod
    def validated_numbers(cls, customs_clearance_number):
        """ 통관 번호 검증 """
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
        """ (오브 젝트 생성) 이메일,유저 네임,비밀 번호 검증 """
        if not cls.validated_email(kwargs.get('email')):
            return False
        elif not cls.validated_nickname(kwargs.get('nickname')):
            return False
        elif not cls.validated_password(kwargs.get('password')):
            return False
        return False

    @classmethod
    def update_validated_user_data(cls, **kwargs):
        """ (오브 젝트 업 데이트) 이메일,유저 네임,비밀번호 검증 """
        email = kwargs.get('email')
        nickname = kwargs.get('nickname')
        password = kwargs.get('password')
        numbers = kwargs.get('numbers')
        if email is not None:
            if not cls.validated_email(email):
                return False
        if nickname is not None:
            if not cls.validated_nickname(nickname):
                return False
        if password is not None:
            if not cls.validated_password(password):
                return False
        if numbers is not None:
            if not cls.validated_numbers(numbers):
                return False
        return True

    @classmethod
    def validated_deliveries(cls, **kwargs):
        # 우편 번호 양식 : https://www.epost.go.kr/search/zipcode/cmzcd003k01.jsp
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
