from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    # Homepage redirects to medicine list
    path('', lambda request: redirect('medicine_list')),  

    # Medicine management
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('add/', views.medicine_add, name='medicine_add'),
    path('edit/<int:id>/', views.medicine_edit, name='medicine_edit'),
    path('delete/<int:id>/', views.medicine_delete, name='medicine_delete'),
    path('sell/<int:id>/', views.medicine_sell, name='medicine_sell'),

    # Sales page
    path('medicines/sales/', views.sales_list, name='sales_list'),

    # Authentication
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
]
