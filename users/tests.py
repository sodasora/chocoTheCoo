from rest_framework.test import APITestCase
from datetime import timedelta
from unittest.mock import patch
from django.utils import timezone
from django.urls import reverse
from django.test.client import (
    MULTIPART_CONTENT,
    encode_multipart,
    BOUNDARY
)
from PIL import Image
import users.models
import users.validated
import json
import tempfile
import os
CALLING_NUMBER = os.environ.get('CALLING_NUMBER')


class CommonTestClass(APITestCase):
    """
    데이터 및 모듈 셋팅 클래스
    """

    @classmethod
    def setUpTestData(cls):
        """
        테스트 클래스 오브젝트 생성
        setUpTestData : 클래스에서 한 번만 실행되고 정의
        """
        # 테스트 유저
        cls.user_data = {'email': 'test@naver.com', "nickanme": "testUser", 'password': 'Test123456!'}
        cls.user = users.models.User.objects.create_user('test@naver.com', "testUser", 'Test123456!')
        cls.user = users.models.User.objects.get(pk=cls.user.pk)

        # 인증 받지 못한 테스트 유저
        cls.another_user_data = {'email': 'anotherUser@email.com', 'nickname': 'another', 'password': 'Test123456!'}
        cls.another_user = users.models.User.objects.create_user('anotherUser@email.com', 'another', 'Test123456!')
        cls.another_user = users.models.User.objects.get(pk=cls.another_user.pk)

        # 소셜 로그인 유저
        cls.kakao_user_data = {'email': 'kakaoUser@email.com', 'nickname': 'kakao', 'password': 'Test123456!'}
        cls.kakao_user = users.models.User.objects.create_user('kakaoUser@email.com', 'kakao', 'Test123456!')
        cls.kakao_user.login_type = 'kakao'
        cls.kakao_user.save()
        cls.kakao_user = users.models.User.objects.get(pk=cls.kakao_user.pk)

    def get_temporary_image(self):
        """
        임시 이미지 파일 생성
        """
        size = (200, 200)
        color = (255, 0, 0, 0)
        temp_file = tempfile.NamedTemporaryFile()
        temp_file.name = "image.png"
        image = Image.new("RGBA", size, color)
        image.save(temp_file, 'png')
        temp_file.seek(0)
        return temp_file


class SignupAPIViewTest(CommonTestClass):
    """
    회원 가입 테스트
    """

    def member_registration_failure_test(self, information, status_code):
        """
        회원 가입 테스트
        """

        url = reverse("user_view")
        response = self.client.post(url, information)
        self.assertEqual(response.status_code, status_code)

    def test_member_registration_failure_test_case(self):
        """
        회원가입 유효성 검사 테스트 케이스
        """

        test_cases = [
            # ({"email": "son@naver.com", "password": "Test123123!", "nickname": "test"}, 200),
            # # 회원 가입 성공 테스트
            # ({"email": "son@naver.com", "password": "Test123123!", "nickname": "test"}, 400),
            # # 회원 가입 실패 테스트 - 같은 이메일 형식으로 가입
            # ({"email": "testnaver.com", "password": "Test123123!", "nickname": "test"}, 400),
            # # 이메일 형식 오류
            # ({"email": "te st@naver.com", "password": "Test123123!", "nickname": "test"}, 400),
            # # 이메일 형식 오류 - 공백이 포함되어 있음
            # ({"email": "test1@navercom", "password": "Test123123!", "nickname": "test"}, 400),
            # # 이메일 형식 오류 - dot 이 없음
            # ({"email": "test2@naver.com", "password": "test123123!", "nickname": "test"}, 200),
            # # 성공 - 영문자 대문자 없어도 가능
            # ({"email": "test3@naver.com", "password": "TEST123123!", "nickname": "test"}, 200),
            # # 성공 - 영문자 소문자 없어도 가능
            # ({"email": "test4@naver.com", "password": "Testtesttest!", "nickname": "test"}, 400),
            # # 비밀번호 형식 오류 - 숫자 없음
            # ({"email": "test5@naver.com", "password": "Test123123", "nickname": "test"}, 400),
            # # 비밀번호 형식 오류 - 특수문자 없음
            # ({"email": "tes6@naver.com", "password": "Aa1!", "nickname": "test"}, 400),
            # # 비밀번호 형식 오류 - 5자의 길이를 충족 못함
            # ({"email": "tes7@naver.com", "password": "Test1 23123!", "nickname": "test"}, 400),
            # # 비밀번호 형식 오류 - 공백이 포함되어 있음
            # ({"email": "test8@naver.com", "password": "Test123123!", "nickname": "tes t"}, 400),
            # # # 닉네임 형식 오류 - 공백이 포함되어 있음
            # ({"email": "test8@naver.com", "password": "Test123123!", "nickname": "t"}, 400),
            # # # 닉네임 형식 오류 - 2자 이상 조건을 충족 못함
            # ({"email": "test9@naver.com", "password": "Test123123!", "nickname": "testtesttesttesttestestsets"}, 400),
            # # # 닉네임 형식 오류 - 20자 이상의 길이를 가짐
            # ({"password": "Test123123!", "nickname": "test"}, 400),
            # # # 이메일 형식 오류 - 값이 없음
            # ({"email": "test10@naver.com", "nickname": "test"}, 400),
            # # # 비밀번호 형식 오류 - 값이 없음
            # ({"email": "test11@naver.com", "password": "Test123123!"}, 400),
            # # 닉네임 형식 오류 - 값이 없음
        ]

        for information, stats_code in test_cases:
            self.member_registration_failure_test(information, stats_code)


class EmailVerificationAndLoginTest(CommonTestClass):
    """
    이메일 인증, 비밀번호 재 설정 , 로그인 테스트
    """

    def setUp(self):
        """
        이메일 인증 코드 발급 받기
        setUp : 메서드가 실행될 때 마다 한 번씩 실행
        """

        url = reverse("email_authentication")
        email = self.user_data.get('email')
        request = {
            "email": email
        }
        response = self.client.post(url, request)
        self.assertEqual(response.status_code, 200)

    def test_fail_login(self):
        """
        이메일 인증을 받지 않은 상태로 로그인 테스트
        """

        response = self.client.post(reverse('login'), self.user_data)
        self.assertEqual(response.status_code, 400)

    def email_verification(self, request, status_code):
        """
        이메일 인증 테스트
        """

        url = reverse("email_authentication")
        response = self.client.put(url, request)
        self.assertEqual(response.status_code, status_code)

        try:
            now_user = users.models.User.objects.get(email=request.get('email'))
            if response.status_code == 200:
                # 계정 활성화 테스트
                self.assertEqual(now_user.is_active, True)
            elif now_user.email == self.user.email:
                # 테스트 케이스중, 이미 인증한 코드로 다시 한번 시도하려는 경우, 계정은 이미 활성화 되어있으므로 예외처리(status code == 400)
                pass
            else:
                self.assertEqual(now_user.is_active, False)
        except users.models.User.DoesNotExist:
            # 가입 되지 않은 유형의 테스트 케이스일 경우
            pass

    def test_email_verification(self):
        """
        이메일 인증 성공, 실패  테스트
        """

        test_cases = [
            ({"email": self.user.email, "verification_code": self.user.email_verification.verification_code[:3]}, 400),
            # 이메일 인증 실패 테스트 - 잘못된 인증 코드 작성
            ({"email": self.another_user.email, "verification_code": self.user.email_verification.verification_code},
             400),
            # 인증 실패 테스트 - 이메일 인증을 받지 않은 사용자가 다른 사람의 인증 코도르 인증 시도
            ({"email": self.user.email, "verification_code": self.user.email_verification.verification_code}, 200),
            # 이메일 인증 성공 테스트
            ({"email": self.user.email, "verification_code": self.user.email_verification.verification_code}, 400),
            # 이메일 인증 실패 테스트 - 이미 인증 성공한 상황 에서 한 번더 인증
            ({"email": 'doesNotExiExist@email.com', "verification_code": 'doesNotExiExistCode'}, 404),
            # 인증 실패 테스트 - 가입 되지 않은 회원
            ({"email": self.kakao_user.email, "verification_code": 'kakaoCode'}, 400),
            # 인증 실패 테스트 - 소셜 계정 사용자가 이메일 인증 시도
        ]
        for information, stats_code in test_cases:
            self.email_verification(information, stats_code)

    def test_email_verification_code_expired(self):
        """
        인증 코드 유효 기간 초과된 사용자가 인증을 시도할 경우
        """

        now = timezone.now() + timedelta(minutes=10)
        with patch('django.utils.timezone.now', return_value=now) as mock_now:
            request = {
                "email": self.user.email,
                "verification_code": self.user.email_verification.verification_code
            }
            self.email_verification(request, 400)

    def login_test(self, information, status_code):
        """
        로그인 테스트
        """

        url = reverse("login")
        response = self.client.post(url, information)
        self.assertEqual(response.status_code, status_code)

    def test_case_login(self):
        """
        로그인 유효성 검사 테스트 케이스
        """

        self.user.is_active = True
        # 이메일 인증 과정 생략
        self.user.save()
        test_cases = [
            ({"email": self.user_data.get('email'), "password": self.user_data.get('password')}, 200),
            # 로그인 성공 테스트
            ({"email": 'unregistered_email@test.com', "password": '123'}, 404),
            # 로그인 실패 테스트 - 가입하지 않은 회원
            ({"email": self.user_data.get('email'), "password": '123'}, 400),
            # 로그인 실패 테스트 - 비밀 번호 틀림
            ({"email": self.another_user_data.get('email'), "password": self.another_user_data.get('password')}, 400),
            # 로그인 실패 테스트 - 이메일 인증을 받지 않아, 활성화 되지 않은 사용자
            ({"email": self.kakao_user_data.get('email'), "password": self.kakao_user_data.get('password')}, 400),
            # 로그인 실패 테스트 - 소셜 계정 사용자가 일반 로그인 경로로 접근 했을 경우
        ]

        for information, stats_code in test_cases:
            self.login_test(information, stats_code)

    def password_reset(self, information, status_code):
        """
        비밀번호 찾기, 재설정 기능 테스트
        사용자가 자신의 비밀번호를 기억하지 못해서 비밀번호를 재 설정하고자 할때
        """

        url = reverse("email_authentication")
        response = self.client.patch(url, information)
        self.assertEqual(response.status_code, status_code)

    def test_case_password_reset(self):
        """
        비밀번호 재 설정 테스트 케이스
        """

        new_password = 'ChangePassword!123'
        [self.login_test({"email": self.user_data.get('email'), "password": '123'}, 400) for _ in range(5)]
        self.assertEqual(self.user.is_active, False)
        # 비밀 번호 5회 틀린 경우 계정 비 활성화

        self.login_test({"email": self.user_data.get('email'), "password": self.user_data.get('password')}, 400)
        # 5회 이상 틀린경우 올바른 비밀 번호로 로그인 시도할경우, 재설정 이전에 로그인 할 수 없음

        test_cases = [
            ({"email": self.user_data.get('email'), "password": self.user_data.get('password'),
              "verification_code": "DoesNotExist"}, 400),
            # 실패 - 잘못된 인증 코드로 접근
            (
            {"email": self.user_data.get('email'), "password": self.user_data.get('password'), "verification_code": ""},
            400),
            # # 실패 - 인증코드 입력값 없음
            ({"email": "", "password": self.user_data.get('password'), "verification_code": "DoesNotExist"}, 404),
            # 실패 - 이메일 정보 입력값이 없음
            ({"email": self.user_data.get('email'), "password": "", "verification_code": "DoesNotExist"}, 400),
            # 실패 - 비밀 번호 입력 값 없음
            ({"email": self.user_data.get('email'), "password": "Password123",
              "verification_code": self.user.email_verification.verification_code}, 400),
            # 실패 - 특수 문자 없음
            ({"email": self.user_data.get('email'), "password": "Password!",
              "verification_code": self.user.email_verification.verification_code}, 400),
            # 실패 - 숫자 없음
            ({"email": self.user_data.get('email'), "password": new_password,
              "verification_code": self.user.email_verification.verification_code}, 200),
            # 성공
            ({"email": self.user_data.get('email'), "password": self.user_data.get('password'),
              "verification_code": self.user.email_verification.verification_code}, 400),
            # 실패 - 같은 인증 코드로 중복 시도
            ({"email": self.kakao_user_data.get('email'), "password": self.kakao_user_data.get('password'),
              "verification_code": self.user.email_verification.verification_code}, 400),
            # 실패 - 소셜 계정
        ]
        for information, stats_code in test_cases:
            self.password_reset(information, stats_code)
            if stats_code == 200:
                is_active = users.models.User.objects.get(email=information.get('email')).is_active
                self.assertEqual(is_active, True)

        self.login_test({"email": self.user_data.get('email'), "password": new_password}, 200)
        # 재 설정한 비밀번호로 로그인 테스트

        encryption_password = users.models.User.objects.get(pk=self.user.pk).password
        # 암호화 테스트
        self.assertNotEqual(new_password, encryption_password)


class UserAPITestCase(CommonTestClass):
    """
    로그인이 필요한 사용자 정보 수정 관련 테스트
    """

    @classmethod
    def setUpTestData(cls):
        """
        테스트 데이터 생성
        """
        # 테스트 유저
        cls.user_data = {'email': 'test@naver.com', "nickanme": "testUser", 'password': 'Test123456!'}
        cls.user = users.models.User.objects.create_user('test@naver.com', "testUser", 'Test123456!')
        cls.user.is_active = True
        cls.user.save()


    def setUp(self):
        """
        토큰 발급
        """

        response = self.client.post(reverse("login"), self.user_data)
        token = json.loads(response.content.decode())
        self.user_refresh_token = token.get('refresh')
        self.user_access_token = token.get('access')


    def edit_password_information(self, information, user_access_token, status_code):
        """
        비밀번호 정보 수정
        """
        response = self.client.put(
            path=reverse("user_view"),
            data=json.dumps(information),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {user_access_token}",
        )
        self.assertEqual(response.status_code, status_code)

    def test_case_edit_password(self):
        """
        비밀번호 수정 테스트 케이스
        """

        new_password = 'ChangePassword!123'
        token = self.user_access_token
        test_cases = [
            ({"password": self.user_data.get('password'), "new_password": "NewPassword123"}, token, 400),
            # 실패 - 특수 문자 없음
            ({"password": self.user_data.get('password'), "new_password": "NewPassword!"}, token, 400),
            # 실패 - 숫자 없음
            ({"password": self.user_data.get('password'), "new_password": new_password}, None, 401),
            # 실패 - 토큰 정보 없음
            ({"password": None, "new_password": new_password}, token, 400),
            # 실패 - 기존 비밀 번호 입력 값 없음
            ({"password": self.user_data.get('password'), "new_password": None}, token, 400),
            # 실패 - 변경하고자 하는 비밀번호 입력 값 없음
            ({"password": "123", "new_password": new_password}, token, 400),
            # 실패 - 비밀번호가 일치하지 않음
            ({"password": self.user_data.get('password'), "new_password": new_password}, token, 200),
            # 성공
        ]
        for information, access_token, stats_code in test_cases:
            self.edit_password_information(information, access_token, stats_code)

        encryption_password = users.models.User.objects.get(pk=self.user.pk).password
        # 암호화 테스트
        self.assertNotEqual(new_password, encryption_password)

    def edit_customs_code(self, information, access_token, status_code):
        """
        통관 번호 정보 수정
        """
        response = self.client.patch(
            path=reverse("user_view"),
            data=json.dumps(information),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, status_code)

    def test_case_edit_customs_code(self):
        """
        통관 번호 수정 테스트 케이스
        """

        customs_code = 'p1234567891'
        token = self.user_access_token
        test_cases = [
            ({"customs_code": customs_code}, token, 200),
            # 성공
            ({"customs_code": "1234567891"}, token, 400),
            # 실패 - 첫 자리수 P가 존재하지 않음
            ({"customs_code": "p12345 891"}, token, 400),
            # 실패 - 공백이 포함 되어 있음
            (None, token, 400),
            # 실패 - 통관 번호 데이터 없음
            ({"customs_code": "p123458913"}, None, 401),
            # 실패 - 토큰 정보 없음
        ]
        for information, access_token, stats_code in test_cases:
            self.edit_customs_code(information, access_token, stats_code)

        encryption_customs_code = users.models.User.objects.get(pk=self.user.pk).customs_code
        # 복호화 진행 되었는지 테스트
        self.assertNotEqual(customs_code, encryption_customs_code)

    def edit_profile_information(self, information, access_token, status_code):
        """
        프로필 정보 수정
        """
        response = self.client.patch(
            path=reverse("update_information"),
            data=encode_multipart(data=information, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, status_code)

    def test_case_edit_profile_information(self):
        """
        프로필 정보 수정 테스트 케이스
        """
        temp_image = self.get_temporary_image()
        token = self.user_access_token
        test_cases = [
            ({"nickname": "rumor", "introduction": "안녕하세요", "profile_image": temp_image}, token, 200),
            # 성공
            ({"nickname": "ru mor", "introduction": "안녕하세요", "profile_image": temp_image}, token, 400),
            # 실패 - 닉네임 형식 요류 : 공백 존재
            ({"nickname": "r", "introduction": "안녕하세요", "profile_image": temp_image}, token, 400),
            # 실패 - 닉네임 형식 요류 : 두 글자 이상 충족 못함
            ({"nickname": "rumorRumor", "introduction": "안녕하세요", "profile_image": temp_image}, token, 400),
            # 실패 - 닉네임 형식 요류 : 아홉 글자 이하 충족 못함
            ({"nickname": "rumor", "introduction": "안녕하세요", "profile_image": temp_image}, None, 401),
            # 실패 - 토큰 정보 없음
        ]
        for information, access_token, stats_code in test_cases:
            self.edit_profile_information(information, access_token, stats_code)

    def get_email_verification_code(self, information, access_token, status_code):
        """
        변경 이메일로 인증 코드 발급 받기
        """

        response = self.client.post(
            path=reverse("update_information"),
            data=json.dumps(information),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, status_code)

    def edit_email_information(self, information, access_token, status_code):
        """
        이메일 정보 변경
        """

        response = self.client.put(
            path=reverse("update_information"),
            data=json.dumps(information),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, status_code)

    def test_case_get_verification_code(self):
        """
        변경할 이메일로 인증 코드 발급 받기 테스트 케이스
        """

        new_email = "changeEamil@test.com"
        token = self.user_access_token
        test_cases = [
            ({"email": new_email}, token, 200),
            # 성공 케이스
            ({"email": new_email}, None, 401),
            # 실패 케이스 : 토큰 정보 없음
            ({"email": "email"}, token, 400),
            # 실패 케이스 : 이메일 형식 오류
            ({"email": "emailnaver.com"}, token, 400),
            ({"email": "email@navercom"}, token, 400),
            ({"email": "email@naver."}, token, 400),
        ]
        for information, access_token, stats_code in test_cases:
            self.get_email_verification_code(information, access_token, stats_code)

    def login_test(self, information, status_code):
        url = reverse("login")
        response = self.client.post(url, information)
        self.assertEqual(response.status_code, status_code)

    def test_edit_email_information(self):
        """
        변경할 이메일로 인증 코드 발급 받기 테스트 케이스
        """

        new_email = "changeEamil@test.com"
        token = self.user_access_token
        response = self.client.post(
            path=reverse("update_information"),
            data=json.dumps({"email": new_email}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        verification_code = self.user.email_verification.verification_code

        test_cases = [
            ({"email": new_email, "verification_code": verification_code}, token, 200),
            # 성공 케이스
            ({"email": new_email, "verification_code": verification_code}, token, 400),
            # 같은 인증 번호 정보로 중복 인증
            ({"email": new_email, "verification_code": verification_code}, None, 401),
            # 실패 케이스 : 토큰 정보 없음
            ({"email": "email.com", "verification_code": verification_code}, token, 400),
            # 실패 케이스 : 이메일 형식 오류
            ({"email": "email.com", "verification_code": "wrong verification code"}, token, 400),
            # 실패 케이스 : 인증 코드 불일치
        ]
        for information, access_token, stats_code in test_cases:
            self.edit_email_information(information, access_token, stats_code)

        login_data = {"email": new_email, "password": self.user_data.get('password')}
        self.login_test(login_data, 200)
        # 변경 이메일로 로그인 테스트

    def test_fail_edit_email_information(self):
        """
        이메일 변경 실패 테스트
        (회원 인증을 위한 유형의 인증 코드를 이메일 변경 인증 코드로 사용할 경우)
        """

        response = self.client.post(reverse("email_authentication"), {"email": self.user_data.get('email')})
        self.assertEqual(response.status_code, 200)
        # 회원 인증용 이메일 인증 코드 발급 받기

        verification_code = self.user.email_verification.verification_code
        information = {
            "verification_code": verification_code
        }
        # 인증 유형이 잘못된 인증 코드로 인증 시도
        self.edit_email_information(information, self.user_access_token, 400)

    def test_email_verification_code_expired(self):
        """
        인증 코드 유효 기간 초과된 인증 코드로
        이메일 변경을 시도할 경우
        """

        new_email = "changeEamil@test.com"
        token = self.user_access_token
        response = self.client.post(
            path=reverse("update_information"),
            data=json.dumps({"email": new_email}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)

        new_email = "changeEamil@test.com"
        url = reverse("email_authentication")
        request = {
            "email": new_email
        }
        self.client.post(url, request)

        now = timezone.now() + timedelta(minutes=10)

        with patch('django.utils.timezone.now', return_value=now) as mock_now:
            information = {
                "verification_code": self.user.email_verification.verification_code
            }
            self.edit_email_information(information, self.user_access_token, 400)

    def test_switch_to_dormant_account(self):
        """
        휴면 계정으로 전환 테스트
        """

        token = self.user_access_token
        response = self.client.delete(
            path=reverse("user_view"),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        is_active = users.models.User.objects.get(pk=self.user.pk).is_active
        # 게정 비활성화 테스트
        self.assertEqual(is_active, False)

        login_information = {
            "email": self.user.email,
            "password": self.user_data.get('password')
        }
        # 휴면 계정으로 전환후 로그인 시도할 경우
        self.login_test(login_information, 400)

    def get_phone_certification(self, information, token, status_code):
        """
        휴대폰 인증 문자 발급 받기 테스트
        """

        response = self.client.put(
            path=reverse("phone_verification"),
            data=json.dumps(information),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, status_code)

    def mobile_phone_verification_test(self, information, token, status_code):
        """
        휴대폰 인증 테스트
        """

        response = self.client.patch(
            path=reverse("phone_verification"),
            data=json.dumps(information),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, status_code)

    """
    문자 발송 제한으로 인해 테스트 코드 모두 작성 후 주석 해제 예정
    """
    # def test_case_mobile_phone_verification(self):
    #     """
    #     핸드폰 인증 번호 발급 테스트 케이스
    #     인증 번호로 휴대폰 인증 테스트
    #     """
    #
    #     phone_number = CALLING_NUMBER
    #     token = self.user_access_token
    #     test_cases = [
    #         # 발송 성공 테스트
    #         ({"phone_number": phone_number}, token, 200),
    #         # 테스트 실패 케이스
    #         ({"phone_number": "010 2345 6789"}, token, 400),
    #         # 공백이 포함된 휴대폰 번호
    #         ({"phone_number": "010-2345-6789"}, token, 400),
    #         # -가 포함된 휴대폰 번호
    #         ({"phone_number": "01086789"}, token, 400),
    #         # 정확하지 않은 핸드폰 번호
    #         ({"phone_number": "공일공일이삼사오육칠팔"}, token, 400),
    #         # 잘못된 입력값
    #         ({"phone_number": "010 2346789"}, token, 400),
    #         # 공백이 포함된 휴대폰 번호
    #         ({"phone_number": phone_number}, None, 401),
    #         # 토큰 정보 없음
    #     ]
    #     for information, access_token, status_code in test_cases:
    #         self.get_phone_certification(information, access_token, status_code)
    #
    #     verification_numbers = self.user.phone_verification.verification_numbers
    #     test_cases = [
    #         # 테스트 실패 케이스 - 잘못된 인증 번호
    #         ({"verification_numbers": "wrong verification code"}, token, 400),
    #         # 토큰 정보 없음
    #         ({"verification_numbers": verification_numbers}, None, 401),
    #         # 테스트 성공 케이스
    #         ({"verification_numbers": verification_numbers}, token, 200),
    #         # 테스트 실패 케이스 - 중복 시도
    #         ({"verification_numbers": verification_numbers}, token, 400),
    #     ]
    #
    #     for information, access_token, status_code in test_cases:
    #         self.mobile_phone_verification_test(information, access_token, status_code)
    #
    #     # 인증 여부 확인
    #     user = admin.models.User.objects.get(pk=self.user.pk)
    #     self.assertEqual(user.phone_verification.is_verified, True)


class DeliveryInformationTestCase(CommonTestClass):
    """
    배송 정보 테스트 케이스
    """

    def setUp(self):
        """
        배송 정보를 위한 사용자 셋팅
        (배송 정보를 기입하기 위해서는 휴대폰 인증을 요구하고 있어, 해당 테스트에서는 핸드폰 인증을 건너 뜀)
        """

        # 테스트 유저
        self.user.is_active = True
        self.user.save()

        # 휴대폰 인증을 받지 않은 유저
        self.another_user.is_active = True
        self.another_user.save()

        # 테스트 유저 accessToken 저장
        response = self.client.post(reverse("login"), self.user_data)
        token = json.loads(response.content.decode())
        self.user_access_token = token.get('access')

        # 테스트 유저2 accessToken 저장 (핸드폰 인증을 받지 않은 사용자)
        response = self.client.post(reverse("login"), self.another_user_data)
        token = json.loads(response.content.decode())
        self.another_user_access_token = token.get('access')

        # 휴대폰 인증
        users.models.PhoneVerification.objects.create(
            user=self.user,
            is_verified=True,
        )
        self.user.save()

    def add_delivery_information_test(self, information, token, status_code):
        """
        배송 정보 추가 테스트
        """

        response = self.client.post(
            path=reverse("delivery"),
            data=json.dumps(information),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, status_code)

    def test_case_add_delivery_information(self):
        """
        배송 정보 추가 테스트 케이스
        """

        my_token = self.user_access_token
        another_user_token = self.another_user_access_token

        test_cases = [
            # 배송 정보 기입 성공 테스트
            ({"address": "우주 왕복 비행선", "detail_address": "306호", "recipient": "우주인", "postal_code": "12345"}, my_token, 200),
            # 상세 주소는 입력값이 없어도 통과
            ({"address": "우주 왕복 비행선", "detail_address": "", "recipient": "우주인", "postal_code": "12345"}, my_token, 200),
            # 실패 케이스 - 토큰 정보 없음
            ({"address": "우주 왕복 비행선", "detail_address": "306호", "recipient": "우주인", "postal_code": "12345"}, None, 401),
            # 실패 케이스 - 우편 번호 형식 오류
            ({"address": "우주 왕복 비행선", "detail_address": "306호", "recipient": "우주인", "postal_code": ""}, my_token, 400),
            ({"address": "우주 왕복 비행선", "detail_address": "306호", "recipient": "우주인", "postal_code": "AA123"}, my_token, 400),
            ({"address": "우주 왕복 비행선", "detail_address": "306호", "recipient": "우주인", "postal_code": "123 45"}, my_token, 400),
            ({"address": "우주 왕복 비행선", "detail_address": "306호", "recipient": "우주인", "postal_code": "1234845"},my_token, 400),
            ({"address": "우주 왕복 비행선", "detail_address": "306호", "recipient": "우주인", "postal_code": "123"}, my_token, 400),
            ({"address": "  ", "detail_address": "306호", "recipient": "우주인", "postal_code": "12345"}, my_token, 400),
            ({"address": "우주 왕복 비행선", "detail_address": "306호", "recipient": "", "postal_code": "12345"}, my_token, 400),
            # 실패 케이스 - 핸드폰 인증을 받지 않은 사용자
            ({"address": "우주 왕복 비행선", "detail_address": "306호", "recipient": "우주인", "postal_code": "12345"}, another_user_token, 400),
        ]
        for information, access_token, status_code in test_cases:
            self.add_delivery_information_test(information, access_token, status_code)

    def read_delivery_information(self, pk, token, status_code):
        response = self.client.get(
            path=reverse("delivery"),
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, status_code)

        if response.status_code == 200:
            response_json = json.loads(response.content.decode())
            return response_json

    def test_add_delivery_information(self):
        """
        배송 정보 다섯개 초과 등록 실패 테스트
        암호화, 복호화 성공 테스트
        """

        token = self.user_access_token
        information = {
            "address": "우주 왕복 비행선",
            "detail_address": "306호",
            "recipient": "우주인",
            "postal_code": "12345"
        }

        # 다섯개 등록 초과 테스트
        for index in range(6):
            status_code = 400 if index == 5 else 200
            self.add_delivery_information_test(information, token, status_code)

        # # 암호화 테스트
        deliveries_data = self.user.deliveries_data.all()
        for element in deliveries_data:
            self.assertNotEqual(element.postal_code, information.get('postal_code'))
            self.assertNotEqual(element.detail_address, information.get('detail_address'))
            self.assertNotEqual(element.recipient, information.get('recipient'))
            self.assertNotEqual(element.address, information.get('address'))

        # # 복호화 테스트
        deliveries_data = self.read_delivery_information(self.user.pk, token, 200)
        for element in deliveries_data:
            self.assertEqual(element.get('postal_code'), information.get('postal_code'))
            self.assertEqual(element.get('detail_address'), information.get('detail_address'))
            self.assertEqual(element.get('recipient'), information.get('recipient'))
            self.assertEqual(element.get('address'), information.get('address'))

    def edit_delivery_information(self, **information):
        """
        배송 정보 수정 테스트
        """

        delivery_id = information.get('delivery_id')
        information = information.get('information')
        token = information.get('token')
        status_code = information.get('status_code')

        response = self.client.put(
            path=reverse("update-delivery", args={"pk": delivery_id}),
            data=json.dumps(information),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, status_code)

    def test_case_edit_delivery_information(self):
        """
        배송 정보 수정 및 삭제 테스트 케이스
        """

        token = self.user_access_token
        information = {
            "address": "우주 왕복 비행선",
            "detail_address": "306호",
            "recipient": "우주인",
            "postal_code": "12345"
        }
        self.add_delivery_information_test(information, token, 200)

        deliveries_data = self.read_delivery_information(self.user.pk, token, 200)

        set_information = {
            "information": {
                "address": "서울시 강남구 스마일 아파트",
                "detail_address": "105동 301호",
                "recipient": "르탄이",
                "postal_code": "53241"
            },
            "token": token,
            "status_code": 200,
            "delivery_id": deliveries_data[0].get('id')
        }