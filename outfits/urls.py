from django.urls import path
from .views import (
    home, OutfitListView, OutfitDetailView, OutfitSearchView,
    create_outfit, cart_view, add_to_cart, update_cart, remove_from_cart,
    user_login, user_logout, register
)

urlpatterns = [
    path('', home, name='home'),
    path('outfits/', OutfitListView.as_view(), name='outfit-list'),
    path('outfits/<int:pk>/', OutfitDetailView.as_view(), name='outfit-detail'),
    path('search/', OutfitSearchView.as_view(), name='outfit-search'),
    path('create/', create_outfit, name='create-outfit'),

    path('cart/', cart_view, name='cart'),
    path('add-to-cart/<int:outfit_id>/', add_to_cart, name='add-to-cart'),
    path('update-cart/<int:item_id>/', update_cart, name='update-cart'),
    path('remove-from-cart/<int:item_id>/', remove_from_cart, name='remove-from-cart'),

    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('register/', register, name='register'),
]
