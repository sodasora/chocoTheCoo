from django.contrib import admin
from chat.models import RoomMessage, ChatRoom, RoomChatParticipant

admin.site.register(ChatRoom)
admin.site.register(RoomMessage)
admin.site.register(RoomChatParticipant)
