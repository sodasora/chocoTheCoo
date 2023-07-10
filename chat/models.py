from django.db import models
from django.contrib.auth.hashers import make_password
from config.models import CommonModel
from users.models import User


class ChatRoom(CommonModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(unique=True, max_length=10, blank=False, null=False)
    desc = models.CharField(max_length=50, blank=False)
    password = models.CharField(max_length=128, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.password:
            self.password = make_password(self.password)
        super(ChatRoom, self).save(*args, **kwargs)


class RoomMessage(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    content = models.TextField(max_length=1000, blank=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class RoomChatParticipant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
