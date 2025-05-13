# dsi202/outfits/urls.py

from django.urls import path
from . import views

app_name = 'outfits'

urlpatterns = [
    path('', views.home, name='home'),
    path('outfits/', views.OutfitListView.as_view(), name='outfit-list'),
    path('outfits/category/<slug:category_slug>/', views.OutfitListView.as_view(), name='outfit_list_by_category'),
    path('outfits/search/', views.OutfitSearchView.as_view(), name='outfit-search'),
    path('outfits/<int:pk>/', views.OutfitDetailView.as_view(), name='outfit-detail'),
    path('outfits/create/', views.create_outfit, name='create-outfit'),

    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:outfit_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/item/update-dates/<int:item_id>/', views.update_cart_item_dates, name='update_cart_item_dates'),

    path('payment/', views.payment_qr_view, name='payment'),
    path('payment/confirm/', views.confirm_payment_view, name='confirm_payment'),
    path('payment/success/', views.payment_success_view, name='payment_success'),
    path('orders/history/', views.order_history_view, name='order_history'),

    path('categories/', views.category_list_view, name='category_list'),

    # Custom auth URLs should be commented out if using allauth
    # path('login/', views.user_login, name='login'),
    # path('logout/', views.user_logout, name='logout'),
    # path('register/', views.register, name='register'),
]