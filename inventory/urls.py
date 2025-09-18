from django.urls import path
from django.shortcuts import redirect
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', lambda request: redirect('medicine_list')),  # redirect homepage → /medicines/
    
    # Medicine management (all protected by login in views)
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('add/', views.medicine_add, name='medicine_add'),
    path('edit/<int:id>/', views.medicine_edit, name='medicine_edit'),
    path('delete/<int:id>/', views.medicine_delete, name='medicine_delete'),
    path('sell/<int:id>/', views.medicine_sell, name='medicine_sell'),

    # Login / Logout
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
]