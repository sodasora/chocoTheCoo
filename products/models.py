from django.db import models
from config.models import CommonModel


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class Product(CommonModel):
    seller = models.ForeignKey('users.Seller', on_delete = models.CASCADE)
    name = models.CharField("상품이름", max_length=100)
    content = models.TextField("상품설명")
    price = models.IntegerField("상품가격")
    amount = models.IntegerField("상품수량")

     # onetomany , foreign key 로!! 
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    image = models.ImageField("상품 이미지", blank=True, null=True)

    def __str__(self):
        return self.name
    
class Review(CommonModel):
    """ 리뷰 """
    user = models.ForeignKey("users.User", models.CASCADE, verbose_name="작성자",)
    product = models.ForeignKey("products.Product", models.CASCADE, verbose_name="상품",)
    title = models.CharField("리뷰 제목", max_length=20)
    content = models.TextField("리뷰 내용", )
    STAR_CHOICES = [
        (1, "⭐"),
        (2, "⭐⭐"),
        (3, "⭐⭐⭐"),
        (4, "⭐⭐⭐⭐"),
        (5, "⭐⭐⭐⭐⭐"),
    ]
    star = models.IntegerField("리뷰 별점", choices=STAR_CHOICES)