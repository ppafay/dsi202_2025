from django.urls import path
from . import views

app_name = 'outfits'

urlpatterns = [
    path('', views.home, name='home'),
    path('outfits/', views.OutfitListView.as_view(), name='outfit-list'),
    path('outfits/search/', views.OutfitSearchView.as_view(), name='outfit-search'),
    path('outfits/<int:pk>/', views.OutfitDetailView.as_view(), name='outfit-detail'),
    path('outfits/create/', views.create_outfit, name='create-outfit'),

    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:outfit_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('payment/', views.payment_qr_view, name='payment'),
    path('payment/confirm/', views.confirm_payment_view, name='confirm_payment'),
    path('orders/history/', views.order_history_view, name='order_history'),

    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
]
