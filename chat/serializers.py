from rest_framework import serializers
from .models import RoomMessage, ChatRoom, RoomChatParticipant


class ChatRoomSerializer(serializers.ModelSerializer):
  class Meta:
      model = ChatRoom
      fields = '__all__'
      read_only_fields = ('created_at', 'updated_at', 'author')


class MessageSerializer(serializers.ModelSerializer):
  author_name = serializers.SerializerMethodField()
  created_at_time = serializers.SerializerMethodField()
  author_image = serializers.SerializerMethodField()

  def get_author_name(self, obj):
      return obj.author.nickname
    
  def get_author_image(self, obj):
    if obj.author.profile_image:
      return obj.author.profile_image.url
    else:
      return None
  
  def get_created_at_time(self, obj):
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


class ParticipantSerializer(serializers.ModelSerializer):
  author_name = serializers.SerializerMethodField()
  
  def get_author_name(self, obj):
        return obj.user.nickname
      
  class Meta:
        model = RoomChatParticipant
        fields = '__all__'