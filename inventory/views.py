from django.shortcuts import render, redirect, get_object_or_404
from .models import Medicine
from .forms import MedicineForm
from django.utils import timezone
from datetime import timedelta

def medicine_list(request):
    medicines = Medicine.objects.all()

    # Add profit calculations for each medicine
    total_profit = 0
    for med in medicines:
        med.profit_per_unit = med.selling_price - med.buying_price
        med.total_profit = med.profit_per_unit * med.quantity
        total_profit += med.total_profit

    # Low-stock alerts: quantity < 10
    low_stock = medicines.filter(quantity__lt=10)

    # Expiry warnings: expiry date within next 30 days
    soon_to_expire = medicines.filter(
        expiry_date__lte=timezone.now().date() + timedelta(days=30)
    )

    context = {
        'medicines': medicines,
        'total_profit': total_profit,
        'low_stock': low_stock,
        'soon_to_expire': soon_to_expire,
        'medicine_count': medicines.count(),
    }
    return render(request, 'inventory/medicine_list.html', context)


def medicine_add(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('medicine_list')
    else:
        form = MedicineForm()
    return render(request, 'inventory/medicine_form.html', {'form': form})


def medicine_edit(request, id):
    medicine = get_object_or_404(Medicine, id=id)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            return redirect('medicine_list')
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'inventory/medicine_form.html', {'form': form})


def medicine_delete(request, id):
    medicine = get_object_or_404(Medicine, id=id)
    if request.method == 'POST':
        medicine.delete()
        return redirect('medicine_list')
    return render(request, 'inventory/medicine_delete.html', {'medicine': medicine})
