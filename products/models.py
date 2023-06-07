from django.db import models
from config.models import CommonModel
# Create your models here.

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
    