from django.contrib import admin
from django.urls import path, include  # <- include is needed

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inventory.urls')),  # <- include your app's URLs
]
