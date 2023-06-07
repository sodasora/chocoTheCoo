from django.db import models
from config.models import CommonModel

class Product(CommonModel):
    pass

class Category(models.Model):
    """ 상품 카테고리 """
    name = models.CharField("카테고리명", max_length=10)

    def __str__(self):
        return str(self.name)
    
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