from django.db import models
from django.utils import timezone
import os
class CommonModel(models.Model):
    """전체 다중 상속 공통 필드"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# 이미지 경로, 파일명 생성함수
def img_upload_to(instance,filename):
    now = timezone.now()
    filename_base, filename_ext = os.path.splitext(filename)
    return "{}_{}{}".format(
        filename_base, now.strftime("%Y%m%d%H%M%S"), filename_ext.lower()
    )