from django.db import models
from config.models import CommonModel
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from datetime import date
from config.models import CommonModel
from .iamport import validation_prepare, get_transaction
import hashlib
import random
import time
from django.db.models.signals import post_save


class UserManager(BaseUserManager):
    """커스텀 유저 매니저"""

    def create_user(self, email, nickname, password=None):
        """관리자 계정 생성"""
        if not password:
            raise ValueError("관리자 계정의 비밀번호는 필수 입력 사항 입니다.")
        elif not nickname:
            raise ValueError("사용자 별명은 필수 입력 사항 입니다.")
        elif not email:
            raise ValueError("사용자 이메일은 필수 입력 사항 입니다.")
        user = self.model(
            email=self.normalize_email(email),
            nickname=nickname,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nickname, password=None):
        """관리자 계정 생성 커스텀"""
        user = self.create_user(
            email,
            password=password,
            nickname=nickname,
        )
        user.is_admin = True
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, CommonModel):
    """Base User model 정의"""

    LOGIN_TYPES = [
        ("normal", "일반"),
        ("kakao", "카카오"),
        ("google", "구글"),
        ("naver", "네이버"),
    ]
    email = models.EmailField("이메일 주소", max_length=100, unique=True)
    nickname = models.CharField("사용자 이름", max_length=20)
    password = models.CharField("비밀번호", max_length=128)
    profile_image = models.ImageField(
        "프로필 이미지", upload_to="%Y/%m", blank=True, null=True
    )
    auth_code = models.CharField("인증 코드", max_length=128, blank=True, null=True)
    login_type = models.CharField(
        "로그인유형", max_length=20, choices=LOGIN_TYPES, default="normal"
    )
    customs_code = models.CharField("통관번호", max_length=20, blank=True, null=True)
    login_attempts_count = models.PositiveIntegerField("로그인 시도 횟수", default=0)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)  # 이메일 인증을 받을시 계정 활성화
    is_seller = models.BooleanField(default=False)  # 판매자 신청 후 관리자 승인하 에 판매 권한 획득
    product_wish_list = models.ManyToManyField(
        "products.Product", symmetrical=False, related_name="wish_lists", blank=True
    )
    review_like = models.ManyToManyField(
        "products.Review",
        symmetrical=False,
        related_name="review_liking_people",
        blank=True,
    )

    # 추가기능 : 핸드폰 번호 https://django-phonenumber-field.readthedocs.io/en/latest/reference.html
    # phone_number

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "password"]
    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class Seller(models.Model):
    """판매자 모델"""

    user = models.OneToOneField(
        "users.User", related_name="user_seller", on_delete=models.CASCADE
    )
    company_name = models.CharField("업체명", max_length=20, unique=True)
    business_number = models.CharField("사업자 등록 번호", max_length=20)
    bank_name = models.CharField("은행 이름", max_length=20)
    account_number = models.CharField("계좌 번호", max_length=30)
    business_owner_name = models.CharField("대표자 성함", max_length=20)
    account_holder = models.CharField("예금주", max_length=20)
    contact_number = models.CharField("업체 연락처", max_length=20)

    def __str__(self):
        """업체명"""
        return self.company_name


class Delivery(models.Model):
    """배송 정보"""

    user = models.ForeignKey(
        "users.User", related_name="deliveries_data", on_delete=models.CASCADE
    )
    address = models.CharField("주소", max_length=100)
    detail_address = models.CharField("상세주소", max_length=100)
    recipient = models.CharField("수령인", max_length=30)
    postal_code = models.CharField("우편번호", max_length=10)

    def __str__(self):
        """수령인"""
        return self.user


class CartItem(CommonModel):
    """장바구니"""

    # * User와 Product의 ManyToManyField
    user = models.ForeignKey(
        "users.User",
        models.CASCADE,
        verbose_name="유저",
    )
    product = models.ForeignKey(
        "products.Product",
        models.CASCADE,
        verbose_name="상품",
    )
    amount = models.PositiveIntegerField("상품개수", default=1)


class Bill(CommonModel):
    """주문내역"""

    user = models.ForeignKey(
        "users.User",
        models.CASCADE,
        verbose_name="유저",
    )
    address = models.CharField("주소", max_length=100)
    detail_address = models.CharField("상세주소", max_length=100)
    recipient = models.CharField("수령인", max_length=30)
    postal_code = models.CharField("우편번호", max_length=10)


class StatusCategory(models.Model):
    """상태 카테고리"""

    name = models.CharField("상태", max_length=20)

    def __str__(self):
        """상태"""
        return self.name


class OrderItem(CommonModel):
    """주문상품"""

    bill = models.ForeignKey("users.Bill", models.CASCADE, verbose_name="주문내역")
    seller = models.ForeignKey("users.Seller", models.CASCADE, verbose_name="판매자")
    status = models.ForeignKey(
        "users.StatusCategory", models.CASCADE, verbose_name="주문상태", default=1
    )
    name = models.CharField("상품명", max_length=100)
    count = models.PositiveIntegerField("상품개수", default=1)
    price = models.PositiveIntegerField("상품가격")
    product_id = models.IntegerField("상품ID")


class PointType(models.Model):
    """포인트 종류: 출석(1), 텍스트리뷰(2), 포토리뷰(3), 구매(4), 충전(5), 사용(6)"""

    title = models.CharField(
        verbose_name="포인트 종류", max_length=10, null=False, blank=False
    )

    def __str__(self):
        return self.title


class Point(CommonModel):
    """포인트 종류: 출석(1), 텍스트리뷰(2), 포토리뷰(3), 구매(4), 충전(5), 사용(6)"""

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="detail_point"
    )
    date = models.DateField("날짜", default=date.today)
    point = models.IntegerField("포인트점수", default=0, null=False, blank=False)
    point_type = models.ForeignKey(PointType, on_delete=models.CASCADE)


class TransactionManager(models.Manager):
    # 새로운 트랜젝션 생성
    def create_new(self, user, amount, type, success=None, transaction_status=None):
        if not user:
            raise ValueError("유저가 확인되지 않습니다.")
        short_hash = hashlib.sha1(str(random.random())).hexdigest()[:2]
        time_hash = hashlib.sha1(str(int(time.time()))).hexdigest()[-3:]
        base = str(user.email).split("@")[0]
        key = hashlib.sha1(short_hash + time_hash + base).hexdigest()[:10]
        new_order_id = "%s" % (key)

        # 아임포트 결제 사전 검증 단계
        validation_prepare(new_order_id, amount)

        # 트랜젝션 저장
        new_trans = self.model(
            user=user, order_id=new_order_id, amount=amount, type=type
        )

        if success is not None:
            new_trans.success = success
            new_trans.transaction_status = transaction_status

        new_trans.save(using=self._db)
        return new_trans.order_id

    # 생선된 트랜잭션 검증
    def validation_trans(self, merchant_id):
        result = get_transaction(merchant_id)

        if result["status"] != "paid":
            return result
        else:
            return None

    def all_for_user(self, user):
        return super(TransactionManager, self).filter(user=user)

    def get_recent_user(self, user, num):
        return super(TransactionManager, self).filter(user=user)[:num]


class Transaction(CommonModel):
    """결제 정보가 담기는 모델"""

    user = models.ForeignKey(
        "users.User", related_name="point_data", on_delete=models.CASCADE
    )
    transaction_id = models.CharField(max_length=120, null=True, blank=True)
    order_id = models.CharField(max_length=120, unique=True)
    amount = models.PositiveIntegerField(default=0)
    success = models.BooleanField(default=False)
    transaction_status = models.CharField(max_length=220, null=True, blank=True)
    type = models.CharField(max_length=120)

    def __str__(self):
        return self.order_id

    class Meta:
        ordering = ["-created_at"]


def new_trans_validation(sender, instance, created, *args, **kwargs):
    if instance.transaction_id:
        # 거래 후 아임포트에서 넘긴 결과
        v_trans = Transaction.objects.validation_trans(merchant_id=instance.order_id)

        res_merchant_id = v_trans["merchant_id"]
        res_imp_id = v_trans["imp_id"]
        res_amount = v_trans["amount"]

        # 데이터베이스에 실제 결제된 정보가 있는지 체크
        r_trans = Transaction.objects.filter(
            order_id=res_merchant_id, transaction_id=res_imp_id, amount=res_amount
        ).exists()

        if not v_trans or not r_trans:
            raise ValueError("비정상적인 거래입니다.")


post_save.connect(new_trans_validation, sender=Transaction)


class Subscribe(CommonModel):
    """소비자구독"""

    user = models.OneToOneField(
        "users.User", related_name="subscribe_data", on_delete=models.CASCADE
    )
    subscribe = models.BooleanField("구독여부", default=True, null=False)
    next_payment = models.DateField("다음결제일")
