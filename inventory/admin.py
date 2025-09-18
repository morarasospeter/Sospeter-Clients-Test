from django.contrib import admin
from .models import Medicine

class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'buying_price', 'selling_price', 'expiry_date', 'manufacturer')

admin.site.register(Medicine, MedicineAdmin)
