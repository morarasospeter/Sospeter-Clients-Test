from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from .models import Medicine, Sale
from .forms import MedicineForm
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict

# ----- LOGIN VIEW -----
def user_login(request):
    error = None
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('medicine_list')
        else:
            error = "Invalid username or password. Please check both fields."
    return render(request, 'inventory/login.html', {'form': form, 'error': error})

# ----- LOGOUT VIEW -----
@login_required
def user_logout(request):
    logout(request)
    return redirect('user_login')

# ----- MEDICINE LIST VIEW (GROUPED BY CATEGORY) -----
@login_required
def medicine_list(request):
    query = request.GET.get('q')
    if query:
        medicines = Medicine.objects.filter(
            Q(name__icontains=query) | Q(manufacturer__icontains=query)
        ).order_by('name')
    else:
        medicines = Medicine.objects.all().order_by('name')

    today_plus_30 = timezone.now().date() + timedelta(days=30)

    # Calculate totals and add extra fields
    total_quantity = 0
    total_stock_value = 0
    for med in medicines:
        med.total_value = med.quantity * med.buying_price
        med.profit_per_unit = med.selling_price - med.buying_price
        total_quantity += med.quantity
        total_stock_value += med.total_value

    # Group medicines by category
    medicines_by_category = defaultdict(list)
    for med in medicines:
        medicines_by_category[med.category].append(med)

    context = {
        'medicines_by_category': medicines_by_category,
        'medicine_count': medicines.count(),
        'total_quantity': total_quantity,
        'total_stock_value': total_stock_value,
        'query': query,
        'today_plus_30': today_plus_30,
    }
    return render(request, 'inventory/medicine_list.html', context)

# ----- MEDICINE ADD -----
@login_required
def medicine_add(request):
    form = MedicineForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('medicine_list')
    return render(request, 'inventory/medicine_form.html', {'form': form})

# ----- MEDICINE EDIT -----
@login_required
def medicine_edit(request, id):
    medicine = get_object_or_404(Medicine, id=id)
    form = MedicineForm(request.POST or None, instance=medicine)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('medicine_list')
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
    error = None
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
            Sale.objects.create(medicine=medicine, quantity_sold=quantity_sold, payment_mode=payment_mode)
            return redirect('sales_list')
        else:
            error = "Invalid quantity. Check stock."

    return render(request, 'inventory/medicine_sell.html', {'medicine': medicine, 'error': error})

# ----- SALES LIST VIEW -----
@login_required
def sales_list(request):
    query = request.GET.get('q')
    sales = Sale.objects.select_related('medicine').all().order_by('-id')

    if query:
        sales = sales.filter(medicine__name__icontains=query)

    today = timezone.now().date()
    daily_sales = sales.filter(sale_date__date=today)

    # Add profit and total sale fields
    for sale in sales:
        sale.profit = (sale.medicine.selling_price - sale.medicine.buying_price) * sale.quantity_sold
        sale.total_sale = sale.medicine.selling_price * sale.quantity_sold
        if not sale.payment_mode:
            sale.payment_mode = "Cash"

    context = {
        'sales': sales,
        'total_profit': sum(sale.profit for sale in sales),
        'daily_total_profit': sum((s.medicine.selling_price - s.medicine.buying_price) * s.quantity_sold for s in daily_sales),
        'daily_total_sales': sum(s.medicine.selling_price * s.quantity_sold for s in daily_sales),
        'daily_total_items_sold': sum(s.quantity_sold for s in daily_sales),
        'query': query,
    }
    return render(request, 'inventory/sales_list.html', context)
