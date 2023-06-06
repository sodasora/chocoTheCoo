from django.db import models
from config.models import CommonModel
from products.models import Product

# Create your models here.

class Cart(CommonModel):
    """ 장바구니 """
    user = models.OneToOneField(User, on_delete=models.CASCADE)

class CartItem(CommonModel):
    """ Cart와 Product의 ManyToManyField """
    product = models.ForeignKey(Product, models.CASCADE, verbose_name="상품", )
    cart = models.ForeignKey(Cart, models.CASCADE, verbose_name="장바구니", )
    count = models.PositiveIntegerField("상품개수", default=1)
    
    