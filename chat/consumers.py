# utils
import json
from datetime import datetime

# channels
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync

# models, serializers
from users.models import User
from chat.models import RoomMessage, ChatRoom, RoomChatParticipant
from chat.serializers import MessageSerializer

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope.get('user')
        room_id = self.scope["url_route"]["kwargs"]["room_id"]
        room = await self.get_room_obj(room_id)
        
        if user.is_authenticated and room:
            self.room_name = self.scope['url_route']['kwargs']['room_id']
            self.room_group_name = 'chat_%s' % self.room_name
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        is_first, participants_count = await self.enter_or_out_room(user.id, room_id, is_enter = True)
        
        if is_first:
            response = {
                'response_type' : "enter",
                'sender': user.id,
                'sender_name': user.nickname,
                'participants_count' : participants_count,
                'user_id' : user.id
            }
            await self.channel_layer.group_send(
                self.room_group_name,
              {
                  'type': 'chat_message',
                  'response': json.dumps(response)
              }
            )
        
        await self.accept()


    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        if self.scope.get('user').is_authenticated:
            user = self.scope.get('user')
            room_id = self.scope['url_route']['kwargs']['room_id']
            participants_count = await self.enter_or_out_room(user.id , room_id, is_enter = False)


        response = {
            'response_type' : "out",
            'participants_count' : participants_count,
            'user_id' : user.id
          }

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'response': json.dumps(response)

            }
          )

    # Receive message from WebSocket
    async def receive(self, text_data):

        text_data_json = json.loads(text_data)
        room_id = text_data_json.get('room_id', '')
        user_id = text_data_json.get('user_id', '')
        
        user = await self.get_user_obj(user_id)
        room = await self.get_room_obj(room_id)

        message = text_data_json['message']
        
        response = {
          'response_type' : "message",
          'message': message,
          'sender': user.id,
          'sender_image': user.profile_image.url,
          'sender_name': user.nickname,
          'room_id': room.id,
          'time': await self.get_time(),
        }        

        if response["sender"] == room.id:
            await self.create_message_obj(user_id, message, room_id)
        else:
            return False
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'response': json.dumps(response)
            }
        )
        

    # Receive message from room group
    async def chat_message(self, event):
        await self.send(text_data=event['response'])


    async def get_time(self):

        now = datetime.now()
        am_pm = now.strftime('%p')      
        now_time = now.strftime('%I:%M')

        if am_pm == 'AM':
          now_time = f"오전 {now_time}"
        else:
          now_time = f"오후 {now_time}"

        return now_time

    @database_sync_to_async
    def get_user_obj(self, user_id):

        try:
            obj = User.objects.get(pk = user_id)
        except User.DoesNotExist:
            return False

        return obj

    @database_sync_to_async
    def get_room_obj(self, room_id):
        try:
            obj=ChatRoom.objects.get(pk=room_id)
        except ChatRoom.DoesNotExist:
            return False
        
        return obj

    @database_sync_to_async
    def create_message_obj(self, user_id, message, room_id):
        obj = RoomMessage.objects.create(author_id=user_id, content=message, room_id = room_id)
        obj.room.save()

        return obj
    
    @database_sync_to_async
    def enter_or_out_room(self, user_id:int, room_id:int, is_enter:bool):
      """
      출/입 에 따라 참여자를 제거/생성|가져오기 를 끝내고 참여자를 반환합니다.
      """

      participants = RoomChatParticipant.objects.filter(room_id = room_id)
      participant, is_first = RoomChatParticipant.objects.get_or_create(room_id = room_id, user_id = user_id)

      if is_enter:
        return is_first, participants.count()
      else:
        participant.delete()
        return is_first, participants.count()
