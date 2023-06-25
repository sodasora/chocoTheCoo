from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    location = settings.AWS_MEDIAFILES_LOCATION

class StaticStorage(S3Boto3Storage):
    location = settings.AWS_STATICFILES_LOCATION