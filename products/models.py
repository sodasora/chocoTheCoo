from django.db import models

# Create your models here.

class Category(models):
    """ 상품 카테고리 """
    name = models.CharField("카테고리명", max_length=10)

    def __str__(self):
        return self.name