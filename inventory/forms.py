from django import forms
from .models import Medicine

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['category', 'name', 'quantity', 'buying_price', 'selling_price', 'expiry_date', 'manufacturer']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'buying_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
        }
