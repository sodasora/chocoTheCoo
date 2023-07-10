from django.urls import path
from chat import views

urlpatterns = [
    path('', views.ChatViewSet.as_view(
        {'get': 'list'}), name='chat_room_list'),
    path('<int:room_id>/',
         views.ChatViewSet.as_view({'get': 'retrieve'}), name='chat_room'),
    path('room/', views.ChatRoomView.as_view(), name='chat_room_post'),
    path('room/<int:room_id>/', views.ChatRoomView.as_view(), name='chat_room_new'),
    path('room/<int:room_id>/<str:password>/',views.ChatViewSet.as_view({'get': 'checkpassword'}), name='chat_room_password'),
]
