from rest_framework import serializers

from users.models import User,Delivery,Seller, Point, Subscribe
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from  .validated import ValidatedData
from .cryption import AESAlgorithm

class UserSerializer(serializers.ModelSerializer):
    """ 유저 회원가입, 업데이트 시리얼 라이저 """
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {"password": {"write_only": True},}

    def validate(self, element):
        """ email,password,username 검사 """
        if self.context == 'create':
            result = ValidatedData.validated_user_data(**element)
            if not result[0]:
                raise serializers.ValidationError(result[1])
        elif self.context == 'update':
            result = ValidatedData.update_validated_user_data(**element)
            if not result[0]:
                raise serializers.ValidationError(result[1])
        return element

    def create(self, validated_data):
        """"  유저 오브젝트 생성  """
        user = super().create(validated_data)
        user.set_password(user.password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """ 유저 오브젝트 업데이트 """
        user = super().update(instance, validated_data)
        validated_data.get('password')
        validated_data.get('numbers')
        user.password = user.set_password(user.password) if validated_data.get('password') != None else user.password
        if validated_data.get('password') != None: # get으로 가져오는 데이터를 변수로 빼둘 것
            user.set_password(user.password)
        if validated_data.get('numbers') == None:
            pass
        else:
            user.numbers = AESAlgorithm.encrypt(user.numbers)
        user.save()
        return user

class DeliverySerializer(serializers.ModelSerializer):
    """  배송 정보 저장  및 업데이트 """
    class Meta:
        model = Delivery
        exclude = ('user',)

    def validate(self, deliveries_data):
        """ 우편 번호 검증 """
        result = ValidatedData.validated_deliveries(**deliveries_data)
        if not result[0]:
            raise serializers.ValidationError(result[1])
        return deliveries_data

    def create(self, validated_data):
        """"  배송 정보 오브젝트 생성 및 암호화 """
        deliveries = super().create(validated_data)
        deliveries.address = AESAlgorithm.encrypt(deliveries.address)
        deliveries.detail_address = AESAlgorithm.encrypt(deliveries.detail_address)
        deliveries.recipient = AESAlgorithm.encrypt(deliveries.recipient)
        deliveries.postal_code = AESAlgorithm.encrypt(deliveries.postal_code)
        deliveries.save()
        return deliveries

    def update(self, instance, validated_data):
        """ 배송 정보 오브젝트 업데이트 및 암호화 """
        deliveries = super().update(instance, validated_data)
        deliveries.address = AESAlgorithm.encrypt(deliveries.address)
        deliveries.detail_address = AESAlgorithm.encrypt(deliveries.detail_address)
        deliveries.recipient = AESAlgorithm.encrypt(deliveries.recipient)
        deliveries.postal_code = AESAlgorithm.encrypt(deliveries.postal_code)
        deliveries.save()
        return deliveries

class SellerSerializer(serializers.ModelSerializer):
    """  판매자 정보 저장 및 업데이트 """
    class Meta:
        model = Seller
        exclude = ('user',)

    def create(self, validated_data):
        """"  판매자 정보  오브젝트 생성 및 암호화 """
        seller_information = super().create(validated_data)
        seller_information.company_name = AESAlgorithm.encrypt(seller_information.company_name)
        seller_information.buisness_number = AESAlgorithm.encrypt(seller_information.buisness_number)
        seller_information.bank_name = AESAlgorithm.encrypt(seller_information.bank_name)
        seller_information.account_number = AESAlgorithm.encrypt(seller_information.account_number)
        seller_information.business_owner_name = AESAlgorithm.encrypt(seller_information.business_owner_name)
        seller_information.account_holder = AESAlgorithm.encrypt(seller_information.account_holder)
        seller_information.contact_number = AESAlgorithm.encrypt(seller_information.contact_number)
        seller_information.save()
        return seller_information

    def update(self, instance, validated_data):
        """ 판매자 정보 오브젝트 업데이트 및 암호화 """
        seller_information = super().update(instance, validated_data)
        seller_information.company_name = AESAlgorithm.encrypt(seller_information.company_name)
        seller_information.buisness_number = AESAlgorithm.encrypt(seller_information.buisness_number)
        seller_information.bank_name = AESAlgorithm.encrypt(seller_information.bank_name)
        seller_information.account_number = AESAlgorithm.encrypt(seller_information.account_number)
        seller_information.business_owner_name = AESAlgorithm.encrypt(seller_information.business_owner_name)
        seller_information.account_holder = AESAlgorithm.encrypt(seller_information.account_holder)
        seller_information.contact_number = AESAlgorithm.encrypt(seller_information.contact_number)
        seller_information.save()
        return seller_information

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """ payload 재정의 """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['nickname'] = user.nickname
        return token

class ReadUserSerializer(serializers.ModelSerializer):
    """ 마이페이지 유저 정보 읽기 """
    deliveries_data = DeliverySerializer(many=True)
    user_seller = SellerSerializer()

    def get_deliveries(self,obj):
        return obj.deliveries_data

    def get_user_seller(self,obj):
        return obj.user_seller

    class Meta:
        model = User
        exclude = ('auth_code','is_admin','is_active','last_login',"created_at","updated_at",'password')

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
        exclude = ('password','auth_code','is_admin','is_active','last_login')
