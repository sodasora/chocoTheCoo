import random,re
from django.core.mail import EmailMessage

def send_email(email):
    """ 인증 메일 발송 """
    code = "".join([str(random.randint(0, 9)) for _ in range(6)])
    title = "ChocoTheCoo"
    string = "초코더쿠에서 회원님의 가입 인증을 위한 코드를 발송했습니다.\n"
    string += "스파르타 코딩클럽 학생들의 팀 프로젝트이니 혹여 요쳥하신적이 없다면 무시해주세요.\n"
    string += "요청하신분이 맞다면, 아래의 인중코드를 인증란에 작성해주십시오.\n"
    string += code
    content = string
    mail = EmailMessage(title,content,to=[email])
    mail.send()
    return code

class ValidatedData():
    """ 데이터 검증 클래스 """
    # 데이터 검증 클래스 설명 https://github.com/sungsu05/B2Coin_algorithm/blob/master/05_30/SonSungSu/test2.py
    @classmethod
    def validated_password(self,password):
        """ 비밀번호 검증 """
        if password == None:
            return False
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        password_match = re.match(password_pattern, password)
        return bool(password_match)

    @classmethod
    def validated_nickname(self,nickname):
        """ 유저네임 검증 """
        check = [
            lambda element: element != None,
            lambda element: len(element) == len(element.replace(" ", "")),
            lambda element: True if (len(element) > 1 and len(element) < 21) else False,
        ]
        for i in check:
            if not i(nickname):
                return False
        return True

    @classmethod
    def validated_email(self,email):
        """ 이메일 검증"""
        if email == None:
            return False
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        email_match = re.match(email_pattern, email)
        return bool(email_match)

    @classmethod
    def validated_user_data(self,**kwargs):
        """ 이메일,유저네임,비밀번호 검증 """
        if not self.validated_email(kwargs.get('email')):
            return [False,"이메일 정보가 올바르지 않습니다."]
        elif not self.validated_nickname(kwargs.get('nickname')):
            return [False,"닉네임이 올바르지 않습니다."]
        elif not self.validated_password(kwargs.get('password')):
            return [False,"비밀번호가 올바르지 않습니다."]
        return [True,"유효성 검사에 통과했습니다."]

    @classmethod
    def validated_deliverie(self,**kwargs):
        # 우편 번호 양식 : https://www.epost.go.kr/search/zipcode/cmzcd003k01.jsp
        postal_code = kwargs.get('postal_code')
        check = [
            lambda element: element != None,
            lambda element: len(element) == len(element.replace(" ", "")),
            lambda element: True if len(element) == 5 else False,
            lambda element: element.isdigit(),
        ]
        for i in check:
            if not i(postal_code):
                return [False,"우편 번호가 정확하지 않습니다."]
        return [True, "우편 번호가 정확합니다."]