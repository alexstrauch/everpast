"""
URL configuration for time_capsule project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/logout/', auth_views.LogoutView.as_view(next_page='/'), name='admin_logout'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('capsules.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

