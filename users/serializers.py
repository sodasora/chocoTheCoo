from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.generics import get_object_or_404
from django.contrib.auth.hashers import check_password
from products.models import Product
from django.db.models import Sum
from datetime import datetime, timedelta
from .validated import ValidatedData, SmsSendView, EmailService
from django.utils import timezone
from .cryption import AESAlgorithm
from users.models import (
    User,
    Delivery,
    Seller,
    Point,
    Subscribe,
    OrderItem,
    PhoneVerification,
)


class UserSerializer(serializers.ModelSerializer):
    """
     유저 회원가입, 업데이트 시리얼 라이저
    """

    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {"password": {"write_only": True}, }

    def validate(self, element):
        """
         email,password,username 검사
         """
        verification_result = ValidatedData.validated_user_data(**element)
        if verification_result is not True:
            raise ValidationError(verification_result[1])
        return element

    def create(self, validated_data):
        """"
        유저 오브 젝트 생성
        """

        user = super().create(validated_data)
        user.set_password(user.password)
        user.save()
        # 이메일 전송
        EmailService.send_email_verification_code(user, user.email, "normal")
        # 포인트 기본값 할당
        # Point.objects.create(point=29900, user_id=user.pk, point_type_id=5)
        return user


class UserUpdatePasswordSerializer(serializers.ModelSerializer):
    """
    비밀번호 수정
    """
    new_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('password', 'new_password')

    def validate(self, attrs):
        """
        비밀번호 데이터 검증
        """

        verification_result = ValidatedData.user_password_update_validation(self.instance, attrs)
        if verification_result is not True:
            raise ValidationError(verification_result[1])
        attrs['password'] = attrs['new_password']
        return attrs

    def update(self, instance, validated_data):
        """
        비밀번호 최신화 및 암호화
        """

        user = super().update(instance, validated_data)
        user.set_password(user.password)
        user.login_attempts_count = 0
        user.save()
        return user


class UserPasswordResetSerializer(serializers.ModelSerializer):
    """
    비밀번호 재 설정 (찾기 기능)
    """
    verification_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('password', 'verification_code', 'email')
        extra_kwargs = {"email": {"read_only": True}, }

    def validate(self, attrs):
        """
        비밀번호 데이터 검증
        """
        verification_result = ValidatedData.validated_email_verification_code(self.instance, attrs.get('verification_code'), 'normal')
        if verification_result is not True:
            # 이메일 인증 코드 검증
            raise ValidationError(verification_result[1])

        if ValidatedData.validated_password(attrs.get('password')) is not True:
            # 비밀번호  검증
            raise ValidationError('5')
        return attrs

    def update(self, instance, validated_data):
        """
        비밀번호 재 설정 및 암호화, 로그인 시도 횟수 초기화, 계정 활성화
        """

        user = super().update(instance, validated_data)
        user.set_password(user.password)
        user.is_active = True
        user.login_attempts_count = 0
        user.save()
        user.email_verification.verification_code = None
        user.email_verification.save()
        return user


class UserUpdateEmailSerializer(serializers.ModelSerializer):
    """
    이메일 정보 수정
    """

    verification_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('verification_code',)

    def validate(self, attrs):
        """
        이메일 정보 검증
        """

        verification_result = ValidatedData.validated_email_verification_code(self.instance, attrs.get('verification_code'), 'change')
        if verification_result is not True:
            # 이메일 인증 코드 유효성 검사
            raise ValidationError(verification_result[1])

        return attrs

    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        user.email = user.email_verification.new_email
        user.save()
        user.email_verification.verification_code = None
        user.email_verification.new_email = None
        user.email_verification.save()
        return user


class UserUpdateCustomsCodeSerializer(serializers.ModelSerializer):
    """
    통관 번호 수정
    """

    class Meta:
        model = User
        fields = ('customs_code',)

    def validate(self, attrs):
        """
        통관 번호 데이터 검증
        """

        verification_result = ValidatedData.validated_customs_code(attrs.get('customs_code'))
        if verification_result is not True:
            raise ValidationError('validation failed')
        return attrs

    def update(self, instance, validated_data):
        """
        통관 번호 최신화 및 암호화
        """

        user = super().update(instance, validated_data)
        customs_code = validated_data.get('customs_code')
        user.customs_code = AESAlgorithm.encrypt(customs_code)
        user.save()
        return user


class UserUpdateProfileSerializer(serializers.ModelSerializer):
    """
    프로필 정보 수정
    """

    class Meta:
        model = User
        fields = ('nickname', 'introduction', 'profile_image')

    def validate(self, attrs):
        """
        통관 번호 데이터 검증
        """

        verification_result = ValidatedData.validated_nickname(attrs.get('nickname'))
        if verification_result is not True:
            raise ValidationError('validation failed')
        return attrs


class DeliverySerializer(serializers.ModelSerializer):
    """
    배송 정보 저장  및 업데이트
    """

    class Meta:
        model = Delivery
        exclude = ('user',)

    def validate(self, deliveries_data):
        """
        배송 정보 유효성 검증
        """

        validated_result = ValidatedData.validated_deliveries(self.context.get('user'), deliveries_data)
        if validated_result is not True:
            raise ValidationError(validated_result[1])
        return deliveries_data

    def encrypt_deliveries_information(self, deliveries, validated_data):
        """
        오브 젝트 암호화
        """

        encrypt_result = AESAlgorithm.encrypt_all(**validated_data)
        deliveries.address = encrypt_result.get('address')
        deliveries.detail_address = encrypt_result.get('detail_address')
        deliveries.recipient = encrypt_result.get('recipient')
        deliveries.postal_code = encrypt_result.get('postal_code')
        deliveries.save()
        return deliveries

    def create(self, validated_data):
        """"
        배송 정보 오브 젝트 생성
        """
        deliveries = super().create(validated_data)
        deliveries = self.encrypt_deliveries_information(deliveries, validated_data)
        deliveries.save()
        return deliveries

    def update(self, instance, validated_data):
        """
        배송 정보 오브 젝트 수정
        """
        deliveries = super().update(instance, validated_data)
        deliveries = self.encrypt_deliveries_information(deliveries, validated_data)
        deliveries.save()
        return deliveries

    def to_representation(self, instance):
        """
        배송지 모델  데이터 복호화
        """
        information = super().to_representation(instance)
        decrypt_result = AESAlgorithm.decrypt_all(**information)
        return decrypt_result


class SellerSerializer(serializers.ModelSerializer):
    """
    판매자 정보 저장 및 업데이트
    """

    # 지난달 대비 수익상승률
    month_growth_rate = serializers.SerializerMethodField()

    def get_month_growth_rate(self, obj):
        current_date = datetime.now()  # 현재시간
        start_of_last_month = current_date.replace(month=current_date.month - 1, day=1, hour=0, minute=0, second=0,
                                                   microsecond=0)  # 지난달 시작일
        start_of_current_month = start_of_last_month.replace(month=start_of_last_month.month + 1, day=1) # 이번달 시작일
        seller_orders1 = OrderItem.objects.filter(seller=obj.pk).filter(order_status=6).filter(
            created_at__gte=start_of_last_month, created_at__lt=start_of_current_month)  # 조건(구매확정:6,지난달)에 맞는 쿼리셋
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # 당월 시작일
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - timedelta(days=1)  # 당월 종료일
        seller_orders2 = OrderItem.objects.filter(seller=obj.pk).filter(order_status=6).filter(
            created_at__gte=start_of_month, created_at__lte=end_of_month)  # 조건(구매확정:6,이번달)에 맞는 쿼리셋
        last_month_profits = sum(order.amount * order.price for order in seller_orders1)
        month_profits = sum(order.amount * order.price for order in seller_orders2)
        return round(((month_profits-last_month_profits) / last_month_profits * 100),2) if last_month_profits else None

    # 이번달 수익
    month_profits = serializers.SerializerMethodField()

    def get_month_profits(self, obj):
        current_date = datetime.now()  # 현재시간
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # 당월 시작일
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - timedelta(days=1)  # 당월 종료일
        seller_orders = OrderItem.objects.filter(seller=obj.pk).filter(order_status=6).filter(
            created_at__gte=start_of_month, created_at__lte=end_of_month)  # 조건(구매확정:6,이번달)에 맞는 쿼리셋
        return sum(order.amount * order.price for order in seller_orders)

    # 누적판매금(거래확정)
    total_profit = serializers.SerializerMethodField()

    def get_total_profit(self, obj):
        seller_orders = OrderItem.objects.filter(seller=obj.pk).filter(order_status=6)  # 조건(구매확정:6)에 맞는 쿼리셋
        return sum(order.amount * order.price for order in seller_orders)

    # 월발송건수(거래확정)
    month_sent = serializers.SerializerMethodField()

    def get_month_sent(self, obj):
        current_date = datetime.now()  # 현재시간
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # 당월 시작일
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - timedelta(days=1)  # 당월 종료일
        sent_orders = OrderItem.objects.filter(seller=obj.pk).filter(order_status=6).filter(
            created_at__gte=start_of_month, created_at__lte=end_of_month)  # 조건(구매확정:6 상태,이번달)에 맞는 쿼리셋
        return len(sent_orders)

    # 발송완료건수(거래확정)
    total_sent = serializers.SerializerMethodField()

    def get_total_sent(self, obj):
        sent_orders = OrderItem.objects.filter(seller=obj.pk).filter(order_status=6)  # 조건(구매확정:6)에 맞는 쿼리셋
        return len(sent_orders)

    # 발송완료주문(거래확정전)
    unpaid_sent = serializers.SerializerMethodField()

    def get_unpaid_sent(self, obj):
        sent_orders = OrderItem.objects.filter(seller=obj.pk).filter(order_status__gte=4,
                                                                     order_status__lt=6)  # 조건(발송완료:4 ~구매확정:6 전 상태)에 맞는 쿼리셋
        return len(sent_orders)

    # 미발송주문
    unsent = serializers.SerializerMethodField()

    def get_unsent(self, obj):
        sent_orders = OrderItem.objects.filter(seller=obj.pk).filter(order_status__gte=2,
                                                                     order_status__lte=3)  # 조건(주문확인중:2 ~발송준비중:3 상태)에 맞는 쿼리셋
        return len(sent_orders)

    # 브랜드좋아요
    followings_count = serializers.SerializerMethodField()

    def get_followings_count(self, obj):
        return obj.user.followings.count()

    # 셀러 팔로우
    is_like = serializers.SerializerMethodField()

    def get_is_like(self, obj):
        request = self.context.get("request")
        if request.user.is_authenticated:
            # 좋아요 object에 포함되 있다면 True 아니라면 False
            return obj.user.followings.filter(pk=request.user.pk).exists()
        return False

    class Meta:
        model = Seller
        exclude = ('user',)

    def encrypt_seller_information(self, seller_information, validated_data):
        """
        오브 젝트 암호화
        """
        encrypt_result = AESAlgorithm.encrypt_all(**validated_data)
        seller_information.bank_name = encrypt_result.get('bank_name')
        seller_information.account_number = encrypt_result.get('account_number')
        seller_information.account_holder = encrypt_result.get('account_holder')
        return seller_information

    def create(self, validated_data):
        """"
        판매자 정보 오브 젝트 생성
        """

        # 유저 테스트 기간 동안 관리자 승인 절차 없이 판매자 자동 승인
        user = self.context.get('user')
        user.is_seller = True
        user.save()
        seller_information = super().create(validated_data)
        seller_information = self.encrypt_seller_information(seller_information, validated_data)
        seller_information.save()
        return seller_information

    def update(self, instance, validated_data):
        """
        판매자 정보 오브 젝트 수정
        """

        seller_information = super().update(instance, validated_data)
        seller_information = self.encrypt_seller_information(seller_information, validated_data)
        seller_information.save()
        return seller_information

    def to_representation(self, instance):
        """
        판매자 모델 데이터 복호화
        """
        information = super().to_representation(instance)
        decrypt_result = AESAlgorithm.decrypt_all(**information)
        return decrypt_result


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    payload 재정의
    """

    def validate(self, attrs):
        user = get_object_or_404(User, email=attrs.get("email"))
        try:
            if user.login_type != 'normal':
                raise ValidationError(f'{user.login_type}로 가입된 소셜 계정입니다.')
            elif user.is_active is False:
                raise ValidationError("휴면 계정입니다.")
            elif user.login_attempts_count >= 5:
                raise ValidationError("비밀 번호 입력 회수가 초과 되었습니다.")
            elif check_password(attrs.get("password"), user.password) is not True:
                user.login_attempts_count += 1
                user.save()
                raise ValidationError(f'비밀번호가 올바르지 않습니다. 남은 로그인 시도 회수 {5 - user.login_attempts_count}')
            else:
                user.last_login = timezone.now()
                user.login_attempts_count = 0
                user.save()
                refresh = RefreshToken.for_user(user)
                access_token = CustomTokenObtainPairSerializer.get_token(user)
                return {"refresh": str(refresh), "access": str(access_token.access_token)}

        except TypeError:
            raise ValidationError("입력값이 없습니다.")

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['nickname'] = user.nickname
        token['is_seller'] = user.is_seller
        try:
            token['subscribe_data'] = user.subscribe_data.subscribe
        except Subscribe.DoesNotExist:
            token['subscribe_data'] = False
        return token


class BriefProductInformation(serializers.ModelSerializer):
    """
    간략한 상품 정보
    """

    class Meta:
        model = Product
        fields = ('id', 'name', 'content', 'image','item_state')


# class SellerInformationSerializer(serializers.ModelSerializer):
#     followings_count = serializers.SerializerMethodField()
#
#     def get_followings_count(self,obj):
#         return obj.followings.count()
#
#     class Meta:
#         model = Product
#         fields = ('user', 'company_img', 'company_name', 'contact_number', 'followings')


class ReadUserSerializer(serializers.ModelSerializer):
    """
    유저 프로필 정보 읽어오기
    """
    product_wish_list = BriefProductInformation(many=True)
    product_wish_list_count = serializers.SerializerMethodField()

    def get_product_wish_list_count(self, obj):
        return obj.product_wish_list.count()



    class Meta:
        model = User

        fields = (
            "profile_image", "nickname", 'id', "email", 'product_wish_list', 'product_wish_list_count', 'introduction',
            'follower'
        )

    def get_user_total_point(self, user_id):
        """
        포인트 합산 내역 정리
        """
        total_plus_point = (
            Point.objects.filter(user_id=user_id)
                .filter(point_type_id__in=[1, 2, 3, 4, 5, 8, 9])
                .aggregate(total=Sum("point"))
        )
        total_minus_point = (
            Point.objects.filter(user_id=user_id)
                .filter(point_type_id__in=[6, 7])
                .aggregate(total=Sum("point"))
        )
        try:
            total_point = total_plus_point["total"] - total_minus_point["total"]
        except TypeError:
            total_point = (
                total_plus_point["total"]
                if total_plus_point["total"] is not None else 0
            )
        return total_point

    def get_seller_information(self, follower):
        """
        팔로우하는 판매자의 더 자세한 정보 뽑아오기
        """
        sellers = follower
        seller_list = []
        for pk in sellers:
            seller = get_object_or_404(Seller, pk=pk)
            company_img = (
                seller.company_img.url if seller.company_img else None
            )
            data = {
                'company_img': company_img,
                'company_name': seller.company_name,
                'user': {
                    'id': seller.user.id,
                },
                'contact_number': seller.contact_number,
                'followings_count': seller.user.followings.count()
            }
            seller_list.append(data)
        return seller_list

    def to_representation(self, instance):
        """
        프로필 정보에 포인트 합산 데이터, 팔로우 하는 판매자 데이터 추가
        """
        information = super().to_representation(instance)
        information["total_point"] = self.get_user_total_point(information.get('id'))
        information["seller_information"] = self.get_seller_information(information.get('follower'))
        information.pop('follower')
        return information


class PointSerializer(serializers.ModelSerializer):
    """
    포인트 시리얼 라이저
    """
    point_category = serializers.SerializerMethodField()

    def get_point_category(self, obj):
        return obj.point_type.title

    class Meta:
        model = Point
        fields = "__all__"
        read_only_fields = ('user', 'point_category', 'point_type')


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    구독 시리얼라이저
    """

    class Meta:
        model = Subscribe
        exclude = ("user", "next_payment")


class SubscriptionInfoSerializer(serializers.ModelSerializer):
    """
    구독 정보 시리얼라이저
    """

    class Meta:
        model = Subscribe
        fields = "__all__"
        read_only_fields = ('user', 'next_payment')


class SellerInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        exclude = ('created_at', 'updated_at')

    def to_representation(self, instance):
        """
        판매자 모델  데이터 복호화
        """
        information = super().to_representation(instance)
        decrypt_result = AESAlgorithm.decrypt_all(**information)
        return decrypt_result


class PhoneVerificationSerializer(serializers.ModelSerializer):
    """
    휴대폰 인증 정보
    """

    class Meta:
        model = PhoneVerification
        exclude = ('user',)

    def validate(self, element):
        """
         휴대폰 번호 유효성 검사
         """
        numbers = element['phone_number']
        if not ValidatedData.validated_phone_number(numbers):
            raise ValidationError("validation failed")
        return element

    def set_cell_phone_information(self, phone_verification, validated_data):
        """
        휴대폰 정보 암호화
        사용자에게 인증 문자 메시지 발송
        """

        numbers = validated_data.get('phone_number')
        phone_verification.phone_number = AESAlgorithm.encrypt(numbers)
        phone_verification.verification_numbers = SmsSendView.get_auth_numbers()
        phone_verification.is_verified = False
        message = f'Choco The Coo에서 인증 번호를 발송 했습니다. [{phone_verification.verification_numbers}]'
        SmsSendView.send_sms(validated_data.get('phone_number'), message)
        phone_verification.save()

    def create(self, validated_data):
        """"
        휴대폰 인증 원투원 필드 생성
        휴대폰 번호 암호화
        """

        phone_verification = super().create(validated_data)
        self.set_cell_phone_information(phone_verification, validated_data)
        return phone_verification

    def update(self, instance, validated_data):
        """
        휴대폰 인증 원투원 필드 업데이트
        휴대폰 번호 복호화
        """

        phone_verification = super().update(instance, validated_data)
        self.set_cell_phone_information(phone_verification, validated_data)
        return phone_verification


class GetSellersInformationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        exclude = ("updated_at",)

    def to_representation(self, instance):
        """
        판매자 데이터 복호화
        """

        information = super().to_representation(instance)
        decryption_list = [
            'account_number',
            'account_holder',
            'bank_name',
            'company_name',
            'account_number',
        ]
        for key, value in information.items():
            if key in decryption_list:
                information[key] = AESAlgorithm.decrypt(value)
            elif key == 'created_at' or key == 'updated_at':
                information[key] = value[:10]
        return information


class UserDetailSerializer(serializers.ModelSerializer):
    """
    사용자 디테일 정보
    """

    user_seller = SellerInformationSerializer()
    deliveries_data = DeliverySerializer(many=True)
    phone_number = serializers.SerializerMethodField()

    def get_phone_number(self, obj):
        try:
            if obj.phone_verification.is_verified is not False:
                # 번호 등록은 했지만, 아직 인증을 하지 않았다면 None값을 반환
                return obj.phone_verification.phone_number
            else:
                return None
        except PhoneVerification.DoesNotExist:
            return None

    class Meta:
        model = User
        fields = (
        "id", "email", "nickname", "profile_image", "customs_code", "introduction", "login_type", 'user_seller',
        'deliveries_data', 'phone_number', 'is_admin')

    def to_representation(self, instance):
        """
        User Model 데이터 복호화
        유저 모델은 복호화할 데이터가 두개 뿐이므로 연산 속도를 위해
        필요한 것만 하나씩 복호화 진행
        """

        information = super().to_representation(instance)
        customs_code = information.get('customs_code')
        if customs_code is not None:
            customs_code = AESAlgorithm.decrypt(customs_code)
            information['customs_code'] = customs_code
        phone_number = information.get('phone_number')
        if phone_number is not None:
            phone_number = AESAlgorithm.decrypt(phone_number)
            information['phone_number'] = phone_number
        return information
