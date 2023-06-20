from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ViewSet
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ChatRoom, RoomMessage
from .serializers import MessageSerializer, ChatRoomSerializer


class ChatViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    
    # 톡방 정보 보여주기
    def list(self, request):
        queryset = ChatRoom.objects.all()
        serializer = ChatRoomSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK) 
    
    # 특정 방의 요청이 'retrive' 오면 채팅방의 채팅 보여주기
    def retrieve(self, request, pk=None): # pk = room_id
        room = get_object_or_404(ChatRoom, pk=pk)
        self.check_object_permissions(request, room)
        RoomMessage.objects.filter(room_id=room.id).exclude(author_id = request.user.id).update(
            is_read=True
        )
        queryset = RoomMessage.objects.filter(room_id=room.id).select_related('author').order_by('created_at')
        serializer = MessageSerializer(queryset, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK) 


# 채팅방 생성(삭제)
class ChatRoomView(APIView):
    def post(self, request):
        serializer = ChatRoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, room_id):
        room = get_object_or_404(ChatRoom, room_id=room_id)
        if request.user == room.author:
            room.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)