from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from .models import Medicine, Sale
from .forms import MedicineForm
from django.utils import timezone
from datetime import timedelta

# ----- LOGIN VIEW -----
def user_login(request):
    error = None
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('medicine_list')
        else:
            error = "Invalid username or password. Please check both fields."
        form = AuthenticationForm(request, data=request.POST)
    else:
        form = AuthenticationForm()

    return render(request, 'inventory/login.html', {'form': form, 'error': error})

# ----- LOGOUT VIEW -----
@login_required
def user_logout(request):
    logout(request)
    return redirect('user_login')

# ----- MEDICINE LIST VIEW (WITH SEARCH, SUMMARY & CHART DATA) -----
@login_required
def medicine_list(request):
    query = request.GET.get('q')
    if query:
        medicines = Medicine.objects.filter(
            Q(name__icontains=query) | Q(manufacturer__icontains=query)
        )
    else:
        medicines = Medicine.objects.all()

    # Calculate low stock and soon to expire
    low_stock = medicines.filter(quantity__lt=10)
    soon_to_expire = medicines.filter(expiry_date__lte=timezone.now().date() + timedelta(days=30))

    # Add extra fields for table display
    for medicine in medicines:
        medicine.total_value = medicine.quantity * medicine.buying_price
        medicine.profit_per_unit = medicine.selling_price - medicine.buying_price

    total_quantity = sum(m.quantity for m in medicines)
    total_stock_value = sum(m.total_value for m in medicines)

    # Calculate date for expiry highlighting
    today_plus_30 = timezone.now().date() + timedelta(days=30)

    context = {
        'medicines': medicines,
        'low_stock': low_stock,
        'soon_to_expire': soon_to_expire,
        'medicine_count': medicines.count(),
        'total_quantity': total_quantity,
        'total_stock_value': total_stock_value,
        'query': query,
        'today_plus_30': today_plus_30,  # pass to template for expiry comparison
    }
    return render(request, 'inventory/medicine_list.html', context)

# ----- MEDICINE ADD -----
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

# ----- MEDICINE EDIT -----
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

# ----- MEDICINE DELETE -----
@login_required
def medicine_delete(request, id):
    medicine = get_object_or_404(Medicine, id=id)
    if request.method == 'POST':
        medicine.delete()
        return redirect('medicine_list')
    return render(request, 'inventory/medicine_delete.html', {'medicine': medicine})

# ----- MEDICINE SELL -----
@login_required
def medicine_sell(request, id):
    medicine = get_object_or_404(Medicine, id=id)
    if request.method == 'POST':
        try:
            quantity_sold = int(request.POST.get('quantity_sold', 0))
            payment_mode = request.POST.get('payment_mode', 'Cash')
        except ValueError:
            error = "Invalid quantity. Enter a number."
            return render(request, 'inventory/medicine_sell.html', {'medicine': medicine, 'error': error})

        if 0 < quantity_sold <= medicine.quantity:
            medicine.quantity -= quantity_sold
            medicine.save()

            sale_data = {'medicine': medicine, 'quantity_sold': quantity_sold}
            if 'payment_mode' in [f.name for f in Sale._meta.fields]:
                sale_data['payment_mode'] = payment_mode

            Sale.objects.create(**sale_data)
            return redirect('sales_list')
        else:
            error = "Invalid quantity. Check stock."
            return render(request, 'inventory/medicine_sell.html', {'medicine': medicine, 'error': error})

    return render(request, 'inventory/medicine_sell.html', {'medicine': medicine})

# ----- SALES LIST VIEW -----
@login_required
def sales_list(request):
    query = request.GET.get('q')
    sales = Sale.objects.select_related('medicine').all().order_by('-id')

    if query:
        sales = sales.filter(medicine__name__icontains=query)

    for sale in sales:
        sale.profit = (sale.medicine.selling_price - sale.medicine.buying_price) * sale.quantity_sold
        sale.total_sale = sale.medicine.selling_price * sale.quantity_sold
        if not hasattr(sale, 'payment_mode') or not sale.payment_mode:
            sale.payment_mode = "Cash"

    total_profit = sum(sale.profit for sale in sales)

    context = {
        'sales': sales,
        'total_profit': total_profit,
        'query': query,
    }
    return render(request, 'inventory/sales_list.html', context)