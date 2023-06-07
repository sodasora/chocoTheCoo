from django.db import models
from config.models import CommonModel
from products.models import Product
from .models import User


class CartItem(CommonModel):
    """
    * 장바구니 
    * User와 Product의 ManyToManyField
    """
    product = models.ForeignKey(Product, models.CASCADE, verbose_name="상품", )
    user = models.ForeignKey(User, models.CASCADE, verbose_name="유저", )
    count = models.PositiveIntegerField("상품개수", default=1)