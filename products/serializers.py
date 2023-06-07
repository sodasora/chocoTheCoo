from rest_framework import serializers
from products.models import Product, Category
from users.models import *



# 카테고리
class CategoryNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name',)

class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')

#상품
class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name')


class ProductDetailSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'content', 'price', 'category', 'image')

class ReviewSerializer(serializers.ModelSerializer):
    """ 리뷰조회에 product_id가 필요, 마이페이지 리뷰 조회는 따로 url과 view를 만들어야 함 """
    class Meta:
        model = Review
        fields = '__all__'

class ReviewDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


