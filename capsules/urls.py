from django.urls import path
from . import views

"""
URL configuration for the capsules app.

This module defines all URL patterns for the time capsule functionality:
- Home page
- Capsule CRUD operations (Create, Read, Update, Delete)
- Capsule content management
- File serving with access control
"""

app_name = 'capsules'

urlpatterns = [
    # Core pages
    path('', views.home, name='home'),
    path('capsules/', views.capsule_list, name='capsule_list'),
    
    # Capsule management
    path('capsule/create/', views.capsule_create, name='capsule_create'),
    path('capsule/<int:pk>/', views.capsule_detail, name='capsule_detail'),
    path('capsule/<int:pk>/edit/', views.capsule_edit, name='capsule_edit'),
    path('capsule/<int:pk>/delete/', views.capsule_delete, name='capsule_delete'),
    path('capsule/<int:pk>/lock/', views.capsule_lock, name='capsule_lock'),
    
    # Content management
    path('capsule/<int:pk>/add-content/', views.content_add, name='content_add'),
    path('content/<int:pk>/edit/', views.content_edit, name='content_edit'),
    path('content/<int:pk>/delete/', views.content_delete, name='content_delete'),
    
    # File serving
    path('content/<int:content_id>/file/', views.serve_protected_file, name='serve_protected_file'),
]
