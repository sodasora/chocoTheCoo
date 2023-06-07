from rest_framework import serializers
from users.models import User,Deliverie,Seller, Point, Subscribe
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from  .validated import ValidatedData

class UserSerializer(serializers.ModelSerializer):
    """ 유저 회원가입, 업데이트 시리얼 라이저 """
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {"password": {"write_only": True},}

    def validate(self, element):
        """ email,password,username 검사 """
        result = ValidatedData.validated_user_data(**element)
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
        user.set_password(user.password)
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
        """"  유저 오브젝트 생성  """
        deliverie = super().create(validated_data)
        """ 개인정보 복호화 알고리즘 필요"""
        return deliverie

    def update(self, instance, validated_data):
        """ 유저 오브젝트 업데이트 """
        deliverie = super().update(instance, validated_data)
        """ 개인정보 복호화 알고리즘 필요"""
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
    """ 테스트용 유저 정보 읽기"""
    deliveries_data = UserDeliverieSerializer(many=True)
    user_seller = SellerSerializer()

    def get_deliveries(self,obj):
        return obj.deliveries_data

    def get_user_seller(self,obj):
        return obj.user_seller

    class Meta:
        model = User
        exclude = ('password','auth_code','is_admin','is_active','last_login')
        

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