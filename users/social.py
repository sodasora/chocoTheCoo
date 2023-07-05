from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.core import files
import os, requests, tempfile
from .models import User, Point
from .serializers import CustomTokenObtainPairSerializer

# REDIRECT_URI = 'https://chocothecoo.com/index.html'
REDIRECT_URI = 'http://127.0.0.1:5501/index.html'
KAKAO_API_KEY = os.environ.get('KAKAO_API_KEY')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_SECRET_KEY = os.environ.get('NAVER_SECRET_KEY')


def SocialLogin(**kwargs):
    """
    소셜 로그인, 회원가입
    """
    email = kwargs.get("email")
    login_type = kwargs.get("login_type")
    if not email:
        return Response(
            {"err": "해당 계정에 email정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        # eamil 오브젝트 불러오기, 실패시 예외 처리로 회원 가입
        user = User.objects.get(email=email)
        if login_type == user.login_type:
            # 휴면 계정으로 전환한 이력이 있다면, 자동 활성화
            user.is_active = True
            user.save()
            # 토큰 발급
            refresh = RefreshToken.for_user(user)
            access_token = CustomTokenObtainPairSerializer.get_token(user)
            return Response(
                {"refresh": str(refresh), "access": str(access_token.access_token)},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": f"{user.login_type}으로 이미 가입된 계정이 있습니다!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except User.DoesNotExist:
        # 사용자 정보 DB에 저장
        new_user = User.objects.create(**kwargs)
        # url image 불러오기
        response = requests.get(new_user.profile_image, stream=True)
        # 파일 이름 재정의
        file_name = ''.join(str(kwargs.get('profile_image')).split('/')[-2:])
        # 임시 파일 생성
        tmp_img = tempfile.NamedTemporaryFile()

        # 이미지 response를 분할로 받기 위함
        for block in response.iter_content(1024 * 8):
            if not block:
                break
            tmp_img.write(block)

        # 프로필 이미지 필드에 저장
        new_user.profile_image.save(file_name, files.File(tmp_img))

        new_user.is_active = True
        new_user.set_unusable_password()
        new_user.save()
        Point.objects.create(point=29900, user_id=new_user.pk, point_type_id=5)
        # 토큰 발급
        refresh = RefreshToken.for_user(new_user)
        access_token = CustomTokenObtainPairSerializer.get_token(new_user)
        return Response(
            {"refresh": str(refresh), "access": str(access_token.access_token)},
            status=status.HTTP_200_OK,
        )


class KakaoLogin(APIView):
    """
    카카오 소셜 로그인
    """

    def get(self, request):
        """
        사용자가 Resource server로 로그인 요청시 Client의 API 인증키 발급
        """
        return Response(KAKAO_API_KEY, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Resource Server가 발급해준 인가 코드 확인
        인가 코드를 이용한 Access Token 발급 받기
        Access Token을 이용하여 사용자가 동의한 추가 제공 정보들 발급 받기
        추가 제공 정보를 토대로 로그인 및 회원가입 진행
        """

        # Resource Server의 인가 코드 확인
        auth_code = request.data.get("code")

        # 인가 코드를 이용한 Token 발급 받기
        # Kakao Token 발급 양식
        # https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#request-token-request-body
        kakao_token_api = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": KAKAO_API_KEY,
            "redirect_uri": REDIRECT_URI,
            "code": auth_code,
        }
        kakao_token = requests.post(
            kakao_token_api,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data,
        )
        # resource server가 발급한 access_token 확인
        access_token = kakao_token.json().get("access_token")

        # access token 을 이용하여 resource server로부터 사용자가 동의한 추가 데이터 사항 불러오기
        user_data = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
            },
        )
        # 데이터 직렬화
        user_data = user_data.json()
        try:
            data = {
                "profile_image": user_data.get("properties").get("profile_image"),
                "nickname": user_data.get("properties").get("nickname"),
                "email": user_data.get("kakao_account").get("email"),
                "login_type": "kakao",
            }
        except AttributeError:
            return Response({"msg": "유효하지 않은 토큰입니다."}, status=status.HTTP_401_UNAUTHORIZED)
        #  로그인 및 회원 가입
        return SocialLogin(**data)


class GoogleLogin(APIView):
    """
    구글 소셜 로그인
    """

    def get(self, request):
        return Response(GOOGLE_API_KEY, status=status.HTTP_200_OK)

    def post(self, request):
        access_token = request.data["access_token"]
        user_data = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_data.json()
        data = {
            "profile_image": user_data.get("picture"),
            "email": user_data.get("email"),
            "nickname": user_data.get("name"),
            "login_type": "google",
        }
        return SocialLogin(**data)


class NaverLogin(APIView):
    """네이버 소셜 로그인"""

    def get(self, request):
        return Response(NAVER_CLIENT_ID, status=status.HTTP_200_OK)

    def post(self, request):
        code = request.data.get("naver_code")
        state = request.data.get("state")
        access_token = requests.post(
            f"https://nid.naver.com/oauth2.0/token?grant_type=authorization_code&code={code}&client_id={NAVER_CLIENT_ID}&client_secret={NAVER_SECRET_KEY}&state={state}",
            headers={"Accept": "application/json"},
        )
        access_token = access_token.json().get("access_token")
        user_data = requests.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        user_data = user_data.json().get("response")
        data = {
            "profile_image": user_data.get("profile_image"),
            "email": user_data.get("email"),
            "nickname": user_data.get("nickname"),
            "login_type": "naver",
        }
        return SocialLogin(**data)