# dsi202/mindvibe_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include(('outfits.urls', 'outfits'), namespace='outfits')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # No need to add static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) for development server
    # if 'django.contrib.staticfiles' is in INSTALLED_APPS and STATICFILES_DIRS is configured.