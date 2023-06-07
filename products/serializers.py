from rest_framework import serializers
from products.models import Product, Category
from users.models import Seller



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


