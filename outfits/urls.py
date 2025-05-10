# project/main/dsi202/outfits/urls.py
from django.urls import path
from . import views
# from django.contrib import admin # ลบออกถ้า admin อยู่ใน project urls
# from django.conf.urls import include # ลบ include ตัวเองออก

# ควรลบ path('accounts/login/', ...) และ path('accounts/logout/', ...)
# ถ้าไม่ได้สร้าง views เหล่านี้ใน outfits/views.py หรือจะใช้ django.contrib.auth.urls

urlpatterns = [
    path('', views.home, name='home'),
    path('outfits/', views.OutfitListView.as_view(), name='outfit-list'),
    path('search/', views.OutfitSearchView.as_view(), name='outfit-search'),
    path('outfits/<int:pk>/', views.OutfitDetailView.as_view(), name='outfit-detail'),
    path('create/', views.create_outfit, name='create-outfit'), # ตรวจสอบว่า rental_form.html คือ create_outfit หรือไม่
    
    path('cart/', views.cart_view, name='cart'),
    # เปลี่ยนพารามิเตอร์เป็น outfit_id
    path('add_to_cart/<int:outfit_id>/', views.add_to_cart, name='add_to_cart'),
    path('update_cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # path('admin/', admin.site.urls), # ย้ายไป project/urls.py
    # path('', include('outfits.urls')), # !!! ลบบรรทัดนี้ออกแน่นอน !!!
    # path('accounts/', include('django.contrib.auth.urls')), # ถ้าจะใช้ auth ของ Django
]