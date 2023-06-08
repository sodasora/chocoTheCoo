from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from datetime import date
from config.models import CommonModel

class UserManager(BaseUserManager):
    """ 커스텀 유저 매니저 """
    def create_user(self, email, nickname, password=None):
        """ 관리자 계정 생성 """
        if not password:
            raise ValueError('관리자 계정의 비밀번호는 필수 입력 사항 입니다.')
        elif not nickname:
            raise ValueError('사용자 별명은 필수 입력 사항 입니다.')
        elif not email:
            raise ValueError('사용자 이메일은 필수 입력 사항 입니다.')
        user = self.model(
            email=self.normalize_email(email),
            nickname=nickname,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nickname, password=None):
        """ 관리자 계정 생성 커스텀 """
        user = self.create_user(
            email,
            password=password,
            nickname=nickname,
        )
        user.is_admin = True
        user.is_active = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    """ Base User model 정의 """
    LOGIN_TYPES = [
        ("normal", "일반"),
        ("kakao", "카카오"),
        ("google", "구글"),
        ("naver", "네이버"),
    ]
    email = models.EmailField("이메일 주소", max_length=100, unique=True)
    nickname = models.CharField("사용자 이름", max_length=20)
    password = models.CharField("비밀번호", max_length=128)
    profile_image = models.ImageField("프로필 이미지",upload_to="%Y/%m", blank=True, null=True)
    auth_code = models.CharField("인증 코드", max_length=128, blank=True, null=True)
    login_type = models.CharField("로그인유형", max_length=20, choices=LOGIN_TYPES, default="normal")
    numbers = models.CharField("통관번호",max_length=20,blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False) # 이메일 인증을 받을시 계정 활성화
    is_seller = models.BooleanField(default=False) # 판매자 신청 후 관리자 승인하 에 판매 권한 획득
    
    """  모델 생성시 연결  """
    # wish_list = models.ManyToManyField('products.Product', symmetrical=False, related_name='wish_lists', blank=True)
    # review_like = models.ManyToManyField('products.Review', symmetrical=False, related_name='liking_people', blank=True)

    # 추가기능 : 핸드폰 번호 https://django-phonenumber-field.readthedocs.io/en/latest/reference.html
    # phone_number

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname','password']
    objects = UserManager()

    def __str__(self):
        return self.nickname

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

class Seller(models.Model):
    """ 판매자 모델 """
    user = models.OneToOneField("users.User", related_name="user_seller", on_delete=models.CASCADE)
    company_name = models.CharField("업체명", max_length=20)
    buisness_number = models.CharField("사업자 등록 번호",max_length=20)
    bank_name = models.CharField("은행 이름",max_length=20)
    account_number = models.CharField("계좌 번호",max_length=30)
    business_owner_name = models.CharField("대표자 성함",max_length=20)
    account_holder = models.CharField("예금주",max_length=20)
    contact_number = models.CharField("업체 연락처",max_length=20)

    def __str__(self):
        """ 업체명 """
        return self.company_name

class Deliverie(models.Model):
    """ 배송 정보  """
    user = models.ForeignKey("users.User",related_name="deliveries_data",on_delete=models.CASCADE)
    address = models.CharField("주소",max_length=100)
    detail_address = models.CharField("상세주소",max_length=100)
    recipient = models.CharField("수령인",max_length=30)
    postal_code = models.CharField("우편번호",max_length=10)

    def __str__(self):
        """ 수령인 """
        return self.recipient


class CartItem(CommonModel):
    """ 장바구니 """
    # * User와 Product의 ManyToManyField
    user = models.ForeignKey("users.User", models.CASCADE, verbose_name="유저", )
    product = models.ForeignKey("products.Product", models.CASCADE, verbose_name="상품", )
    count = models.PositiveIntegerField("상품개수", default=1)

# class Bill(CommonModel):
#     """ 주문내역 """
#     user = models.ForeignKey("users.User", models.CASCADE, verbose_name="유저", )
#     address = models.CharField("주소", max_length=100)
#     detail_address = models.CharField("상세주소", max_length=100)
#     recipient = models.CharField("수령인", max_length=30)
#     postal_code = models.CharField("우편번호", max_length=10)

class StatusCategory(models.Model):
    """ 상태 카테고리 """
    name = models.CharField("상태", max_length=20)

# class OrderItem(CommonModel):
#     """ 주문상품 """
#     bill = models.ForeignKey("users.Bill", models.CASCADE, verbose_name="주문내역")
#     seller = models.ForeignKey("users.Seller", models.CASCADE, verbose_name="판매자")
#     status = models.ForeignKey("users.StatusCategory", models.CASCADE, verbose_name="주문상태")
#     name = models.CharField("상품명", max_length=100)
#     count = models.PositiveIntegerField("상품개수", default=1)
#     price = models.PositiveIntegerField("상품가격")
#     product_id = models.IntegerField("상품ID")

class PointType(models.Model):
    """포인트 종류: 출석(1), 리뷰(2), 구매(3), 사용(4)"""
    title = models.CharField(verbose_name="포인트 종류", max_length=10, null=False, blank=False)
    
    def __str__(self):
        return self.title


class Point(models.Model):
    """포인트"""
    user = models.ForeignKey("users.User",related_name="point_data",on_delete=models.CASCADE)
    date = models.DateField("날짜",default=date.today)
    points = models.IntegerField("포인트점수", null=False, blank=False)
    point_type = models.ForeignKey(PointType, on_delete=models.CASCADE)
    

class Subscribe(CommonModel):
    """소비자구독"""
    user = models.OneToOneField("users.User",related_name="subscribe_data",on_delete=models.CASCADE)
    subscribe = models.BooleanField("구독여부", default=True, null=False)
    next_payment = models.DateField("다음결제일")

