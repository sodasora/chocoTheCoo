from django.urls import path
from chat import consumers

websocket_urlpatterns = [
    # 로컬 url
    path("ws/chat/<str:room_id>/", consumers.ChatConsumer.as_asgi()),
    # 도커 url
    # path("chat/<str:room_id>/", consumers.ChatConsumer.as_asgi()),
]
