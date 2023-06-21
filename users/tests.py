from rest_framework.test import APITestCase
from datetime import timedelta
import users.models
import users.validated
from unittest.mock import patch
from django.utils import timezone
from django.urls import reverse


class SignupAPIViewTest(APITestCase):
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
            ({"email": "son@naver.com", "password": "Test123123!", "nickname": "test"}, 200),
            # 회원 가입 성공 테스트
            ({"email": "son@naver.com", "password": "Test123123!", "nickname": "test"}, 400),
            # 회원 가입 실패 테스트 - 같은 이메일 형식으로 가입
            ({"email": "testnaver.com", "password": "Test123123!", "nickname": "test"}, 400),
            # 이메일 형식 오류
            ({"email": "te st@naver.com", "password": "Test123123!", "nickname": "test"}, 400),
            # 이메일 형식 오류 - 공백이 포함되어 있음
            ({"email": "test1@navercom", "password": "Test123123!", "nickname": "test"}, 400),
            # 이메일 형식 오류 - dot 이 없음
            ({"email": "test2@naver.com", "password": "test123123!", "nickname": "test"}, 400),
            # 비밀번호 형식 오류 - 대문자 없음
            ({"email": "test3@naver.com", "password": "TEST123123!", "nickname": "test"}, 400),
            # 비밀번호 형식 오류 - 소문자 없음
            ({"email": "test4@naver.com", "password": "Testtesttest!", "nickname": "test"}, 400),
            # 비밀번호 형식 오류 - 숫자 없음
            ({"email": "test5@naver.com", "password": "Test123123", "nickname": "test"}, 400),
            # 비밀번호 형식 오류 - 특수문자 없음
            ({"email": "tes6@naver.com", "password": "Aa1!", "nickname": "test"}, 400),
            # 비밀번호 형식 오류 - 8자의 길이를 충족 못함
            ({"email": "tes7@naver.com", "password": "Test1 23123!", "nickname": "test"}, 400),
            # 비밀번호 형식 오류 - 공백이 포함되어 있음
            ({"email": "test8@naver.com", "password": "Test123123!", "nickname": "tes t"}, 400),
            # 닉네임 형식 오류 - 공백이 포함되어 있ㅇ므
            ({"email": "test8@naver.com", "password": "Test123123!", "nickname": "t"}, 400),
            # 닉네임 형식 오류 - 2자 이상 조건을 충족 못함
            ({"email": "test9@naver.com", "password": "Test123123!", "nickname": "testtesttesttest"}, 400),
            # 닉네임 형식 오류 - 10자 이상의 길이를 가짐
            ({"password": "Test123123!", "nickname": "test"}, 400),
            # # 이메일 형식 오류 - 값이 없음
            ({"email": "test10@naver.com", "nickname": "test"}, 400),
            # # 비밀번호 형식 오류 - 값이 없음
            ({"email": "test11@naver.com", "password": "Test123123!"}, 400),
            # 닉네임 형식 오류 - 값이 없음
        ]

        for information, stats_code in test_cases:
            self.member_registration_failure_test(information, stats_code)



class EmailVerificationAndLoginTest(APITestCase):
    """
    이메일 인증, 로그인 테스트
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
        response = self.client.put(url, request)
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

        url = reverse("user_view")
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
            ({"email": self.another_user.email, "verification_code": self.user.email_verification.verification_code}, 400),
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


    def password_reset(self,information,status_code):
        """
        비밀번호 찾기, 재설정 기능 테스트
        사용자가 자신의 비밀번호를 기억하지 못해서 비밀번호를 재 설정하고자 할때
        """

        url = reverse("user_view")
        response = self.client.patch(url, information)
        self.assertEqual(response.status_code, status_code)

    def test_case_password_reset(self):

        [self.login_test({"email": self.user_data.get('email'), "password": '123'}, 400) for _ in range(5)]
        self.assertEqual(self.user.is_active,False)
        # 비밀 번호 5회 틀린 경우 계정 비 활성화

        self.login_test({"email": self.user_data.get('email'), "password": self.user_data.get('password')}, 400)
        # 5회 이상 틀린경우 올바른 비밀 번호로 로그인 시도할경우, 재설정 이전에 로그인 할 수 없음

        test_cases = [
            ({"email": self.user_data.get('email'), "password": self.user_data.get('password'), "verification_code": "DoesNotExist"}, 400),
            # 비밀번호 재 설정 테스트 (실패) - 잘못된 인증 코드로 접근
            ({"email": self.user_data.get('email'), "password": self.user_data.get('password'), "verification_code": self.user.email_verification.verification_code}, 200),
            # 비밀번호 재 설정 테스트 (성공)
            ({"email": self.user_data.get('email'), "password": self.user_data.get('password'), "verification_code": self.user.email_verification.verification_code}, 400),
            # 비밀번호 재 설정 테스트 (실패) - 같은 인증 코드로 중복 시도
            ({"email": "DoesNotExist", "password": "DoesNotExist", "verification_code": "DoesNotExist"}, 404),
            # 비밀번호 재 설정 테스트 (실패)  - 이메일 정보를 잘못 기입한 경우 또는 가입 하지 않은 이메일 정보


        ]

        for information, stats_code in test_cases:
            self.password_reset(information, stats_code)
            if stats_code == 200:
                is_active = users.models.User.objects.get(email=information.get('email')).is_active
                self.assertEqual(is_active, True)