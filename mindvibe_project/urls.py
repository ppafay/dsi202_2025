from django.contrib import admin
from django.urls import path, include # ตรวจสอบว่า include ถูก import
from django.conf import settings
from django.conf.urls.static import static
from outfits.views import payment_qr_view, order_history_view
from outfits import views

urlpatterns = [
    path('', include(('outfits.urls', 'outfits'), namespace='outfits')), 
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('payment/qr/', payment_qr_view, name='payment_qr'),
    path('orders/history/', views.order_history_view, name='order_history'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)