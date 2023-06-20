from django.contrib import admin
from chat.models import RoomMessage, ChatRoom

admin.site.register(ChatRoom)
admin.site.register(RoomMessage)
