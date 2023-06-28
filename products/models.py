from django.db import models
from config.models import CommonModel, img_upload_to


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Product(CommonModel):
    seller = models.ForeignKey("users.Seller", on_delete=models.CASCADE)
    name = models.CharField("상품이름", max_length=100)
    content = models.TextField("상품설명")
    price = models.IntegerField("상품가격", null=True, default=0)
    amount = models.IntegerField("상품수량", null=True, default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField("상품 이미지", upload_to=img_upload_to, blank=True, null=True)
    ITEM_STATE_CHOICES = [
        (1, "판매중"),
        (2, "품절"),
        (3, "단종"),
        (4, "비공개"),
        (5, "차단됨"),
        (6, "삭제됨"),
    ]
    item_state = models.PositiveIntegerField(
        max_length=10,
        choices=ITEM_STATE_CHOICES,
        default=1,
    )

    def __str__(self):
        return self.name


class Review(CommonModel):
    """리뷰"""

    user = models.ForeignKey(
        "users.User",
        models.CASCADE,
        verbose_name="작성자",
    )
    product = models.ForeignKey(
        "products.Product",
        models.CASCADE,
        verbose_name="상품",
        related_name="product_reviews",
    )
    title = models.CharField("리뷰제목", max_length=20)
    content = models.TextField(
        "리뷰내용",
    )
    image = models.ImageField("리뷰이미지", upload_to=img_upload_to, blank=True, null=True)
    STAR_CHOICES = [
        (1, "⭐"),
        (2, "⭐⭐"),
        (3, "⭐⭐⭐"),
        (4, "⭐⭐⭐⭐"),
        (5, "⭐⭐⭐⭐⭐"),
    ]
    star = models.IntegerField("리뷰 별점", choices=STAR_CHOICES)

    class Meta:
        ordering = ["-updated_at"]
