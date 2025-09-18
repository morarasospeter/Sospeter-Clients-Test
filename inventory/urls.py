from django.urls import path
from . import views

urlpatterns = [
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('add/', views.medicine_add, name='medicine_add'),
    path('edit/<int:id>/', views.medicine_edit, name='medicine_edit'),
    path('delete/<int:id>/', views.medicine_delete, name='medicine_delete'),
]
