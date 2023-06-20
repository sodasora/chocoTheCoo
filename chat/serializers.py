from rest_framework import serializers
from .models import RoomMessage, ChatRoom

class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = '__all__'
        read_only_fields = ('created_at','updated_at')


class MessageSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_author(self, obj):
        return obj.author.nickname
    
    def get_created_at(self, obj):
        time = obj.created_at
        am_pm = time.strftime('%p')
        now_time = time.strftime('%I:%M')

        if am_pm == 'AM':
          now_time = f"오전 {now_time}"
        else:
          now_time = f"오후 {now_time}"
        return now_time

    class Meta:
        model = RoomMessage
        fields = '__all__'
