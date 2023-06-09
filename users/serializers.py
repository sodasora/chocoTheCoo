from rest_framework import serializers
from users.models import User,Delivery,Seller, Point, Subscribe
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .validated import ValidatedData
from .cryption import AESAlgorithm


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
                raise "입력값이 올바르지 않습니다."
        elif self.context == 'update':
            verification_result = ValidatedData.update_validated_user_data(**element)
            if not verification_result:
                raise "입력값이 올바르지 않습니다."
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
        validated_data.get('password')
        validated_data.get('numbers')
        user.password = user.set_password(user.password) if validated_data.get(
            'password') is not None else user.password
        user.numbers = AESAlgorithm.encrypt(user.numbers) if validated_data.get('numbers') is not None else user.numbers
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
        verification_result = ValidatedData.validated_deliveries(**deliveries_data)
        if not verification_result:
            raise "우편 정보가 올바르지 않습니다."
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


class SellerSerializer(serializers.ModelSerializer):
    """
    판매자 정보 저장 및 업데이트
    """

    class Meta:
        model = Seller
        exclude = ('user',)

    def encrypt_seller_information(self, seller_information, validated_data):
        """
        오브 젝트 암호화
        """
        encrypt_result = AESAlgorithm.encrypt_all(**validated_data)
        seller_information.company_name = encrypt_result.get('company_name')
        seller_information.business_number = encrypt_result.get('business_number')
        seller_information.bank_name = encrypt_result.get('bank_name')
        seller_information.account_number = encrypt_result.get('account_number')
        seller_information.business_owner_name = encrypt_result.get('business_owner_name')
        seller_information.account_holder = encrypt_result.get('account_holder')
        seller_information.contact_number = encrypt_result.get('contact_number')
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


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    payload 재정의
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['nickname'] = user.nickname
        return token


class ReadUserSerializer(serializers.ModelSerializer):
    """
    유저 정보 읽기
    """

    class Meta:
        model = User
        exclude = ('auth_code', 'is_admin', 'is_active', 'last_login', "created_at", "updated_at", 'password')

# class ReadUserSerializer(serializers.ModelSerializer):
#     """
#     마이 페이지 유저 정보 읽기
#     """
#     deliveries_data = DeliverySerializer(many=True)
#     user_seller = SellerSerializer()
#
#     def get_deliveries(self, obj):
#         return obj.deliveries_data
#
#     def get_user_seller(self, obj):
#         return obj.user_seller
#
#     class Meta:
#         model = User
#         exclude = ('auth_code', 'is_admin', 'is_active', 'last_login', "created_at", "updated_at", 'password')

class PointSerializer(serializers.ModelSerializer):
    """포인트 시리얼라이저"""
    class Meta:
        modle = Point
        fields = "__all__"
        
class SubscriptionSerializer(serializers.ModelSerializer):
    """구독시리얼라이저"""
    class Meta:
        model = Subscribe
        fields = "__all__" 
        exclude = ('password','auth_code','is_admin','is_active','last_login')

