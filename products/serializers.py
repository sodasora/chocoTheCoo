from rest_framework import serializers
import users.models
from products.models import Product, Category, Review
from users.models import OrderItem, User


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
        return round(sum(star.star for star in product_stars)/len(product_stars), 1) if product_stars else None # 리뷰가 존재한다면 평균값 리턴, 없다면 None


    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('seller',)


class GetReviewUserListInfo(serializers.ModelSerializer):
    """
    리뷰 정보 불러오기
    """

    review_liking_people = serializers.SerializerMethodField()
    review_liking_people_count = serializers.SerializerMethodField()
    user_profile_image = serializers.SerializerMethodField()

    def get_review_liking_people(self, obj):
        """
        리뷰 좋아요 누른 사람의 id값 반환
        """

        people_id = [user.pk for user in obj.review_liking_people.all()]
        return people_id

    def get_review_liking_people_count(self, obj):
        """
        리뷰 좋아요 누른 사람 count 값 반환
        """

        return obj.review_liking_people.count()

    def get_user_profile_image(self, obj):
        """
        리뷰 작성자의 프로필 이미지 반환
        """

        if obj.user.profile_image:
            return str(obj.user.profile_image)
        return None

    class Meta:
        model = Review
        fields = "__all__"



class SimpleSellerInformation(serializers.ModelSerializer):
    """
    간단한 판매자 정보 리스트
    """
    class Meta:
        model = users.models.Seller
        fields = ('company_img','company_name','user','business_owner_name','contact_number')


class GetProductDetailSerializer(serializers.ModelSerializer):
    """
    상품 상세 조회
    """
    seller = SimpleSellerInformation()
    product_reviews = GetReviewUserListInfo(many=True)
    product_information = serializers.SerializerMethodField()

    def get_product_information(self, obj):
        # 다른 시리얼 라이저 데이터 불러오기
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