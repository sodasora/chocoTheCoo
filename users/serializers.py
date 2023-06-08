from rest_framework import serializers
from users.models import User,Deliverie,Seller
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
        print(user)
        user.set_password(user.password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """ 유저 오브젝트 업데이트 """
        user = super().update(instance, validated_data)
        if validated_data.get('password') != None:
            user.set_password(user.password)
        if validated_data.get('numbers') != None:
            user.numbers = AESAlgorithm.encrypt(user.numbers)
        user.save()
        return user

class DeliverieSerializer(serializers.ModelSerializer):
    """  주소지 저장  및 업데이트 """
    class Meta:
        model = Deliverie
        exclude = ('user',)

    def validate(self, deliverie_data):
        """ 우편 번호 검증 """
        result = ValidatedData.validated_deliverie(**deliverie_data)
        if not result[0]:
            raise serializers.ValidationError(result[1])
        return deliverie_data

    def create(self, validated_data):
        """"  배송 정보 오브젝트 생성 및 암호화 """
        deliverie = super().create(validated_data)
        deliverie.address = AESAlgorithm.encrypt(deliverie.address)
        deliverie.detail_address = AESAlgorithm.encrypt(deliverie.detail_address)
        deliverie.recipient = AESAlgorithm.encrypt(deliverie.recipient)
        deliverie.postal_code = AESAlgorithm.encrypt(deliverie.postal_code)
        deliverie.save()
        return deliverie

    def update(self, instance, validated_data):
        """ 배송 정보 오브젝트 업데이트 및 암호화 """
        deliverie = super().update(instance, validated_data)
        deliverie.address = AESAlgorithm.encrypt(deliverie.address)
        deliverie.detail_address = AESAlgorithm.encrypt(deliverie.detail_address)
        deliverie.recipient = AESAlgorithm.encrypt(deliverie.recipient)
        deliverie.postal_code = AESAlgorithm.encrypt(deliverie.postal_code)
        deliverie.save()
        return deliverie

class SellerSerializer(serializers.ModelSerializer):
    """  판매자 정보 저장 및 업데이트 """
    class Meta:
        model = Seller
        exclude = ('user',)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """ payload 재정의 """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['nickname'] = user.nickname
        return token

class UserDeliverieSerializer(serializers.ModelSerializer):
    """ 사용자 배송 정보 """
    class Meta:
        model = Deliverie
        exclude = ('user',)

class ReadUserSerializer(serializers.ModelSerializer):
    """ 마이페이지 유저 정보 읽기 """
    deliveries_data = UserDeliverieSerializer(many=True)
    user_seller = SellerSerializer()

    def get_deliveries(self,obj):
        return obj.deliveries_data

    def get_user_seller(self,obj):
        return obj.user_seller

    class Meta:
        model = User
        exclude = ('auth_code','is_admin','is_active','last_login',"created_at","updated_at",'password')

    def decrypt(self, element):
        """ 데이터 복호화 """
        if element.get('numbers') != None:
            """ 통관 번호 복호화 """
            numbers = AESAlgorithm.decrypt(element['numbers'])
            element['numbers'] = numbers
        for value in element['deliveries_data']:
            """ 주소지 복호화 """
            address = AESAlgorithm.decrypt(value['address'])
            detail_address = AESAlgorithm.decrypt(value['detail_address'])
            recipient = AESAlgorithm.decrypt(value['recipient'])
            postal_code = AESAlgorithm.decrypt(value['postal_code'])
            value['address'] = address
            value['detail_address'] = detail_address
            value['recipient'] = recipient
            value['postal_code'] = postal_code
        return element
