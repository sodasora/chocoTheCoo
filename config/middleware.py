from users.models import User
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.db import close_old_connections
from urllib.parse import parse_qs
# from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
# from rest_framework_simplejwt.tokens import UntypedToken
# from jwt import decode as jwt_decode
# from django.conf import settings


@database_sync_to_async
def get_user(user_id):
    try:
        user = get_user_model().objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        close_old_connections()
        try:
            user_id = parse_qs(scope["query_string"].decode("utf8"))["id"][0]
        except KeyError:
            scope["user"] = AnonymousUser()
            return await super().__call__(scope, receive, send)

        if user_id:
            scope["user"] = await get_user(user_id=user_id)
        else:
            scope["user"] = AnonymousUser()
        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))
