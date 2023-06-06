from django.db import models

class CommonModel(models.Model):
    """ 전체 다중 상속 공통 필드 """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True