# dsi202/mindvibe_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include(('outfits.urls', 'outfits'), namespace='outfits')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')), # For django-allauth
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # For development, Django automatically serves static files from STATICFILES_DIRS
    # and from app's 'static' subdirectories if 'django.contrib.staticfiles' is in INSTALLED_APPS.
    # So, the following line might not be strictly necessary but doesn't harm:
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # STATIC_ROOT is for collectstatic in prod