from django.urls import path
from chat import consumers

websocket_urlpatterns = [
    path("ws/chat/<str:room_id>/", consumers.ChatConsumer.as_asgi()),
]
