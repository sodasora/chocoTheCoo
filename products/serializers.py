from rest_framework import serializers
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
        return sum(star.star for star in product_stars)/len(product_stars) if product_stars else None # 리뷰가 존재한다면 평균값 리턴, 없다면 None


    class Meta:
        model = Product
        fields = '__all__'


class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


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
