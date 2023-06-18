from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.generics import get_object_or_404
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.http import JsonResponse
from products.models import Product
from django.db.models import Sum
from datetime import datetime, timedelta
from .validated import ValidatedData, SmsSendView
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
        if self.context == 'create':
            verification_result = ValidatedData.validated_user_data(**element)
            if not verification_result:
                raise ValidationError("입력값이 올바르지 않습니다.")
        elif self.context == 'update':
            verification_result = ValidatedData.update_validated_user_data(**element)
            if not verification_result:
                raise ValidationError("입력값이 올바르지 않습니다.")
        return element

    def create(self, validated_data):
        """"
        유저 오브 젝트 생성
        """
        user = super().create(validated_data)
        user.set_password(user.password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        유저 오브 젝트 업데이트
        """

        user = super().update(instance, validated_data)
        customs_code = validated_data.get('customs_code')
        if validated_data.get('password') is not None:
            user.set_password(user.password)
        user.customs_code = AESAlgorithm.encrypt(customs_code) if customs_code is not None else user.customs_code
        user.save()
        return user


class DeliverySerializer(serializers.ModelSerializer):
    """
    배송 정보 저장  및 업데이트
    """

    class Meta:
        model = Delivery
        exclude = ('user',)

    def validate(self, deliveries_data):
        """
        우편 번호 검증
        """
        verification_result = ValidatedData.validated_postal_code(**deliveries_data)
        if not verification_result:
            raise ValidationError("우편 정보가 올바르지 않습니다.")
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
        end_of_last_month = start_of_last_month.replace(month=start_of_last_month.month + 1, day=1) - timedelta(
            days=1)  # 지난달 종료일
        seller_orders1 = OrderItem.objects.filter(seller=obj.id).filter(order_status=5).filter(
            created_at__gte=start_of_last_month, created_at__lte=end_of_last_month)  # 조건(구매확정:5,지난달)에 맞는 쿼리셋
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # 당월 시작일
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - timedelta(days=1)  # 당월 종료일
        seller_orders2 = OrderItem.objects.filter(seller=obj.id).filter(order_status=5).filter(
            created_at__gte=start_of_month, created_at__lte=end_of_month)  # 조건(구매확정:5,이번달)에 맞는 쿼리셋
        last_month_profits = sum(order.amount * order.price for order in seller_orders1)
        month_profits = sum(order.amount * order.price for order in seller_orders2)
        return (month_profits - last_month_profits) / last_month_profits if last_month_profits else None

    # 이번달 수익
    month_profits = serializers.SerializerMethodField()

    def get_month_profits(self, obj):
        current_date = datetime.now()  # 현재시간
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # 당월 시작일
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - timedelta(days=1)  # 당월 종료일
        seller_orders = OrderItem.objects.filter(seller=obj.id).filter(order_status=5).filter(
            created_at__gte=start_of_month, created_at__lte=end_of_month)  # 조건(구매확정:5,이번달)에 맞는 쿼리셋
        return sum(order.amount * order.price for order in seller_orders)

    # 누적판매금(거래확정)
    total_profit = serializers.SerializerMethodField()

    def get_total_profit(self, obj):
        seller_orders = OrderItem.objects.filter(seller=obj.id).filter(order_status=5)  # 조건(구매확정:5)에 맞는 쿼리셋
        return sum(order.amount * order.price for order in seller_orders)

    # 월발송건수(거래확정)
    month_sent = serializers.SerializerMethodField()

    def get_month_sent(self, obj):
        current_date = datetime.now()  # 현재시간
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # 당월 시작일
        end_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1) - timedelta(days=1)  # 당월 종료일
        sent_orders = OrderItem.objects.filter(seller=obj.id).filter(order_status=5).filter(
            created_at__gte=start_of_month, created_at__lte=end_of_month)  # 조건(구매확정:5 상태,이번달)에 맞는 쿼리셋
        return len(sent_orders)

    # 발송완료건수(거래확정)
    total_sent = serializers.SerializerMethodField()

    def get_total_sent(self, obj):
        sent_orders = OrderItem.objects.filter(seller=obj.id).filter(order_status=5)  # 조건(구매확정:5)에 맞는 쿼리셋
        return len(sent_orders)

    # 발송완료주문(거래확정전)
    unpaid_sent = serializers.SerializerMethodField()

    def get_unpaid_sent(self, obj):
        sent_orders = OrderItem.objects.filter(seller=obj.id).filter(order_status__gte=4,
                                                                     order_status__lt=5)  # 조건(배송중:4 ~구매확정:5 전 상태)에 맞는 쿼리셋
        return len(sent_orders)

    # 미발송주문
    unsent = serializers.SerializerMethodField()

    def get_unsent(self, obj):
        sent_orders = OrderItem.objects.filter(seller=obj.id).filter(order_status__gte=2,
                                                                     order_status__lte=3)  # 조건(주문확인:2 ~배송준비중:3 상태)에 맞는 쿼리셋
        return len(sent_orders)

    # 판매기간
    ''' seller 등록일 created_at을 만들것인가? 논의 필요'''

    # sale_terms = serializers.SerializerMethodField()
    # def get_sale_terms(self, obj):
    #     current_date = datetime.now() # 현재시간
    #     # term = obj.created_at
    #     return (current_date) 

    # 브랜드좋아요 - 구현방법 상의 후 구현

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

    @classmethod
    def validate(self, attrs):
        user = get_object_or_404(User, email=attrs.get("email"))
        try:
            if user.is_active is False:
                raise ValidationError("휴면 계정입니다.")
            elif user.login_attempts_count >= 5:
                raise ValidationError("비밀 번호 입력 회수가 초과 되었습니다.")
            elif check_password(attrs.get("password"), user.password) is not True:
                user.login_attempts_count += 1
                user.save()
                raise ValidationError(f'비밀번호가 올바르지 않습니다. 남은 로그인 시도 회수 {5 - user.login_attempts_count}')
            else:
                user.login_attempts_count = 0
                user.last_login = timezone.now()
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
        fields = ('id', 'name', 'content', 'image')


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
        "profile_image", "nickname", 'id', "email", 'product_wish_list', 'product_wish_list_count', 'introduction')

    def to_representation(self, instance):
        """
        프로필 정보에 포인트 합산 데이터 추가
        """
        information = super().to_representation(instance)
        total_plus_point = (
            Point.objects.filter(user_id=information.get('id'))
                .filter(point_type_id__in=[1, 2, 3, 4, 5])
                .aggregate(total=Sum("point"))
        )
        total_minus_point = (
            Point.objects.filter(user_id=information.get('id'))
                .filter(point_type_id=6)
                .aggregate(total=Sum("point"))
        )
        try:
            total_point = total_plus_point["total"] - total_minus_point["total"]
        except TypeError:
            total_point = (
                total_plus_point["total"]
                if total_plus_point["total"] is not None else 0
            )
        information["total_point"] = total_point
        return information


class BriefUserInformation(serializers.ModelSerializer):
    """
    간략한 사용자 정보
    """

    class Meta:
        model = User
        fields = ("profile_image", "nickname", 'id')


class GetWishListUserInfo(serializers.ModelSerializer):
    """
    상품 찜 등록한  유저들 정보 불러오기
    """
    wish_lists = BriefUserInformation(many=True)
    wish_lists_count = serializers.SerializerMethodField()

    def get_wish_lists_count(self, obj):
        return obj.wish_lists.count()

    class Meta:
        model = User
        fields = ('wish_lists', 'wish_lists_count')


class GetReviewUserListInfo(serializers.ModelSerializer):
    """
    리뷰 좋아요 유저들 정보 불러오기
    """
    review_liking_people = BriefUserInformation(many=True)
    review_liking_people_count = serializers.SerializerMethodField()

    def get_review_liking_people_count(self, obj):
        return obj.review_liking_people.count()

    class Meta:
        model = User
        fields = ('review_liking_people', 'review_liking_people_count')


class FollowSerializer(serializers.ModelSerializer):
    """
    팔로우 정보 불러오기
    """
    followings = BriefUserInformation(many=True)
    followings_count = serializers.SerializerMethodField()

    def get_followings_count(self, obj):
        return obj.followings.count()

    class Meta:
        model = User
        fields = ('followings', 'followings_count')


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
            raise ValidationError("핸드폰 번호가 올바르지 않습니다.")
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
        fields = ("id", "email", "nickname", "profile_image", "customs_code", "introduction", "login_type", 'user_seller', 'deliveries_data', 'phone_number')

    def to_representation(self, instance):
        """
        User Model 데이터 복호화
        유저 모델은 복호화할 데이터가 두개 뿐이므로 연산 속도를 위해
        필요한 것만 하나씩 복호화 진행
        """

        information = super().to_representation(instance)
        customs_code = information.get('customs_code')
        if customs_code is not None:
            customs_code = AESAlgorithm.encrypt(customs_code)
            information['customs_code'] = customs_code
        phone_number = information.get('phone_number')
        if phone_number is not None:
            phone_number = AESAlgorithm.encrypt(phone_number)
            information['phone_number'] = phone_number

        return information
