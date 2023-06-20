from django.urls import path
from chat import views

urlpatterns = [
    path('', views.ChatViewSet.as_view(
        {'get': 'list'}), name='chat_room_list'),
    path('room/', views.ChatRoomView.as_view(), name='chat_room_post'),
    path('room/<int:room_id>', views.ChatRoomView.as_view(), name='chat_room_post'),
    path('<int:pk>/',
         views.ChatViewSet.as_view({'get': 'retrieve'}), name='chat_room'),
]
