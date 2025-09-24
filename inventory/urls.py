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

    # Sell medicines
    path('sell/', views.medicine_sell, name='medicine_sell'),               # Multiple medicines
    path('sell/<int:medicine_id>/', views.medicine_sell, name='medicine_sell'),  # Single medicine

    # Sale receipt
    path('sales/receipt/<int:sale_id>/', views.sale_receipt, name='sale_receipt'),

    # Sales list
    path('medicines/sales/', views.sales_list, name='sales_list'),

    # Delete a sale
    path('sales/delete/<int:sale_id>/', views.sale_delete, name='sale_delete'),

    # Authentication
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
]
