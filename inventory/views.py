from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import Medicine, Sale
from .forms import MedicineForm
from django.utils import timezone
from datetime import timedelta

# ----- LOGIN VIEW -----
def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # AuthenticationForm already validates the credentials
            user = form.get_user()
            login(request, user)
            return redirect('medicine_list')
    else:
        form = AuthenticationForm()
    
    return render(request, 'inventory/login.html', {'form': form})

# ----- LOGOUT VIEW -----
@login_required
def user_logout(request):
    logout(request)
    return redirect('user_login')

# ----- MEDICINE VIEWS (Require login) -----
@login_required
def medicine_list(request):
    medicines = Medicine.objects.all()

    # Low-stock alerts: quantity < 10
    low_stock = medicines.filter(quantity__lt=10)

    # Expiry warnings: expiry date within next 30 days
    soon_to_expire = medicines.filter(
        expiry_date__lte=timezone.now().date() + timedelta(days=30)
    )

    # Total profit from all sales
    sales = Sale.objects.all()
    total_profit = sum(sale.profit() for sale in sales)

    context = {
        'medicines': medicines,
        'total_profit': total_profit,
        'low_stock': low_stock,
        'soon_to_expire': soon_to_expire,
        'medicine_count': medicines.count(),
    }
    return render(request, 'inventory/medicine_list.html', context)

@login_required
def medicine_add(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('medicine_list')
    else:
        form = MedicineForm()
    return render(request, 'inventory/medicine_form.html', {'form': form})

@login_required
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

@login_required
def medicine_delete(request, id):
    medicine = get_object_or_404(Medicine, id=id)
    if request.method == 'POST':
        medicine.delete()
        return redirect('medicine_list')
    return render(request, 'inventory/medicine_delete.html', {'medicine': medicine})

@login_required
def medicine_sell(request, id):
    medicine = get_object_or_404(Medicine, id=id)
    
    if request.method == 'POST':
        quantity_sold = int(request.POST.get('quantity_sold', 0))
        if quantity_sold > 0 and quantity_sold <= medicine.quantity:
            # Reduce stock
            medicine.quantity -= quantity_sold
            medicine.save()

            # Record the sale
            Sale.objects.create(medicine=medicine, quantity_sold=quantity_sold)

            return redirect('medicine_list')
        else:
            error = "Invalid quantity. Check stock."
            return render(request, 'inventory/medicine_sell.html', {'medicine': medicine, 'error': error})

    return render(request, 'inventory/medicine_sell.html', {'medicine': medicine})