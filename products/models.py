from django.db import models
from config.models import CommonModel
from users.models import User

class Category(models.Model):
    """ 상품 카테고리 """
    name = models.CharField("카테고리명", max_length=10)

    def __str__(self):
        return str(self.name)
    
class Review(CommonModel):
    user = models.ForeignKey(User, verbose_name="작성자", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="상품", on_delete=models.CASCADE)
    title = models.CharField("리뷰 제목", max_length=20)
    content = models.TextField("리뷰 내용", )
    STAR_CHOICES = [
        (1, "⭐"),
        (2, "⭐⭐"),
        (3, "⭐⭐⭐"),
        (4, "⭐⭐⭐⭐"),
        (5, "⭐⭐⭐⭐⭐"),
    ]
    star = models.IntegerField("리뷰 별점", max_length=1, choices=STAR_CHOICES)
