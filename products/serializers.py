from rest_framework import serializers
from products.models import Product, Category, Review


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
        read_only_fields = ('product_name', 'product_star')


class ReviewDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"
