import time

from rest_framework import serializers
from users.models import Seller
from products.models import Product, Category, Review
from users.models import OrderItem, User
import json

# 카테고리
class CategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category

        fields = "__all__"


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category

        fields = ("id", "name")


# 상품
class ProductListSerializer(serializers.ModelSerializer):
    
    # 누적판매량 OrderItem table에서 amount 조회 + filter(order_status = 6 ) 6: 구매확정 
    sales = serializers.SerializerMethodField()
    def get_sales(self, obj):
        product_sales = OrderItem.objects.filter(product_id=obj.id).filter(order_status=6) # 조건(구매확정)에 맞는 쿼리셋
        return sum(sale.amount for sale in product_sales)
    
    # 상품 찜(likes) 갯수 User table 에서 wish 조회
    likes = serializers.SerializerMethodField()
    def get_likes(self, obj):
        product_likes = User.objects.filter(product_wish_list=obj.id) # 조건(해당상품 찜 내역)에 맞는 쿼리셋
        return len(product_likes) if product_likes else 0

    # 평점(별점) Review table 에서 star 조회
    stars = serializers.SerializerMethodField()
    def get_stars(self, obj):
        product_stars = Review.objects.filter(product=obj.id) # 조건(해당상품의 리뷰)에 맞는 쿼리셋
        return round(sum(star.star for star in product_stars)/len(product_stars), 1) if product_stars else 0 # 리뷰가 존재한다면 평균값 리턴, 없다면 None


    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('seller',)


class UserProfileInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'profile_image', 'nickname')


class GetReviewUserListInfo(serializers.ModelSerializer):
    """
    리뷰 정보 불러오기
    """

    review_liking_people_count = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    user = UserProfileInformationSerializer()

    def get_is_like(self, obj):
        request = self.context.get("request")
        if request.user.is_authenticated:
            # 좋아요 object에 포함되 있다면 True 아니라면 False
            return obj.review_liking_people.filter(pk=request.user.pk).exists()
        return False

    def get_review_liking_people_count(self, obj):
        """
        리뷰 좋아요 누른 사람 count 값 반환
        """

        return obj.review_liking_people.count()


    class Meta:
        model = Review
        exclude = ('created_at',)

    def set_choices_value(self,choice_list, value):
        """
        쵸이스 필드 value값 탐색
        """
        for key, label in choice_list:
            if key == value:
                return label
        return None

    def to_representation(self, instance):
        information = super().to_representation(instance)

        # 쵸이스 필드에 맞는 값 조정
        information['service_evaluation'] = self.set_choices_value(self.Meta.model.SERVICE_EVALUATION, information['service_evaluation'])
        information['feedback_evaluation'] = self.set_choices_value(self.Meta.model.FEEDBACK_EVALUATION, information['feedback_evaluation'])
        information['delivery_evaluation'] = self.set_choices_value(self.Meta.model.DELIVERY_EVALUATION, information['delivery_evaluation'])
        # 수정일
        information['updated_at'] = information.get('updated_at')[:10]
        return information


class SimpleSellerInformation(serializers.ModelSerializer):
    """
    간단한 판매자 정보 리스트
    """
    followings_count = serializers.SerializerMethodField()
    is_follow = serializers.SerializerMethodField()
    def get_is_follow(self, obj):
        """
        get 요청한 사용자가 팔로우중인지 판단.
        """
        request = self.context.get("request")
        if request.user.is_authenticated:
            return obj.user.followings.filter(pk=request.user.pk).exists()
        return False


    def get_followings_count(self, obj):
        return obj.user.followings.count()

    class Meta:
        model = Seller
        fields = ('company_img', 'company_name', 'user', 'business_owner_name', 'contact_number', 'is_follow', 'followings_count')


class GetProductDetailSerializer(serializers.ModelSerializer):
    """
    상품 상세 조회
    """
    seller = SimpleSellerInformation()
    product_reviews = GetReviewUserListInfo(many=True)
    product_information = serializers.SerializerMethodField()
    in_wishlist = serializers.SerializerMethodField()
    delivery_evaluation = serializers.SerializerMethodField()
    service_evaluation = serializers.SerializerMethodField()
    feedback_evaluation = serializers.SerializerMethodField()

    def get_delivery_evaluation(self, obj):
        """
        배송 리뷰 평가 종합하기
        """
        delivery_counts = {
            "good": obj.product_reviews.filter(delivery_evaluation="good").count(),
            "normal": obj.product_reviews.filter(delivery_evaluation="normal").count(),
            "bad": obj.product_reviews.filter(delivery_evaluation="bad").count(),
        }
        return delivery_counts

    def get_service_evaluation(self, obj):
        """
        서비스 리뷰 평가 종합 하기
        """
        service_counts = {
            "good": obj.product_reviews.filter(service_evaluation="good").count(),
            "normal": obj.product_reviews.filter(service_evaluation="normal").count(),
            "bad": obj.product_reviews.filter(service_evaluation="bad").count(),
        }
        return service_counts

    def get_feedback_evaluation(self, obj):
        """
        피드백 리뷰 평가 종합 하기
        """
        feedback_counts = {
            "good": obj.product_reviews.filter(feedback_evaluation="good").count(),
            "normal": obj.product_reviews.filter(feedback_evaluation="normal").count(),
            "bad": obj.product_reviews.filter(feedback_evaluation="bad").count(),
        }
        return feedback_counts

    def get_in_wishlist(self, obj):
        """
        get 요청 사용자가 상품을 찜 등록 했는지 판단.
        """

        request = self.context.get("request")
        if request.user.is_authenticated:
            return obj.wish_lists.filter(pk=request.user.pk).exists()
        return False

    def get_product_information(self, obj):
        """
        해당 product의 통계치 불러오기
        """

        new_dict = {
            "sales": ProductListSerializer(obj).data.get('sales'),
            "likes": ProductListSerializer(obj).data.get('likes'),
            "stars": ProductListSerializer(obj).data.get('stars'),
        }
        return new_dict

    class Meta:
        model = Product
        fields = "__all__"


class ProductDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ('seller',)


class ReviewSerializer(serializers.ModelSerializer):
    """
    상품페이지에서는 리뷰조회에 product_id가 필요, 마이페이지에서는 x
    프론트에서 보내주고, 조건문으로 보내주는 값을 다르게.
    """
    
    product_name= serializers.SerializerMethodField()
    product_star = serializers.SerializerMethodField()
    
    def get_product_name(self, obj):
        return obj.product.name
    
    def get_product_star(self, obj):
        return obj.star * '⭐'

    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ('product_name', 'product_star', 'user', 'product')


class ReviewDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ('product_name', 'product_star', 'user', 'product')