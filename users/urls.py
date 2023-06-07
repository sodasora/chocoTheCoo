from django.urls import path
from .views import CartView, CartDetailView

urlpatterns = [
    path("<int:user_id>/carts/", CartView.as_view()),
    path("<int:user_id>/carts/<int:cart_item_id>/", CartDetailView.as_view()),
]
