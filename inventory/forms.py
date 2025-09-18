from django import forms
from .models import Medicine

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'quantity', 'buying_price', 'selling_price', 'expiry_date', 'manufacturer']
