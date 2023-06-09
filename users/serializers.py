from rest_framework import serializers
from rest_framework.serializers import ValidationError
from users.models import User,Delivery,Seller, Point, Subscribe
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .validated import ValidatedData
from .cryption import AESAlgorithm
from products.models import Product

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
        password = validated_data.get('password')
        customs_code = validated_data.get('customs_code')
        if password is not None:
            user.set_password(password)
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
        verification_result = ValidatedData.validated_deliveries(**deliveries_data)
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

class BriefProductInformation(serializers.ModelSerializer):
    """
    간략한 상품 정보
    """
    class Meta:
        model = Product
        fields = ('id','name','content','image')



class ReadUserSerializer(serializers.ModelSerializer):
    """
    유저 정보 읽기
    """
    product_wish_list = BriefProductInformation(many=True)
    product_wish_list_count = serializers.SerializerMethodField()

    def get_product_wish_list_count(self, obj):
        return obj.product_wish_list.count()

    class Meta:
        model = User
        fields = ("profile_image","nickname",'id',"email",'product_wish_list','product_wish_list_count')

class BriefUserInformation(serializers.ModelSerializer):
    """
    간략한 사용자 정보
    """
    class Meta:
        model = User
        fields = ("profile_image","nickname",'id')

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
        fields = ('wish_lists','wish_lists_count')

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
        fields = ('review_liking_people','review_liking_people_count')


class PointSerializer(serializers.ModelSerializer):
    """포인트 시리얼라이저"""
    class Meta:
        model = Point
        fields = "__all__"
        
class SubscriptionSerializer(serializers.ModelSerializer):
    """구독시리얼라이저"""
    class Meta:
        model = Subscribe
        fields = "__all__" 

