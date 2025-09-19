from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q, Sum
from .models import Medicine, Sale
from .forms import MedicineForm
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict

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
            error = "Invalid username or password."
        form = AuthenticationForm(request, data=request.POST)
    else:
        form = AuthenticationForm()
    return render(request, 'inventory/login.html', {'form': form, 'error': error})

# ----- LOGOUT VIEW -----
@login_required
def user_logout(request):
    logout(request)
    return redirect('user_login')

# ----- MEDICINE LIST VIEW -----
@login_required
def medicine_list(request):
    query = request.GET.get('q', '')
    medicines = Medicine.objects.all()

    if query:
        medicines = medicines.filter(Q(name__icontains=query) | Q(manufacturer__icontains=query))

    # Calculate totals
    total_quantity = medicines.aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_stock_value = sum(m.quantity * m.buying_price for m in medicines)

    today_plus_30 = timezone.now().date() + timedelta(days=30)

    # Group medicines by category
    medicines_by_category = defaultdict(list)
    for med in medicines:
        # Add display fields
        med.stock_status_text = med.stock_status()
        med.expiry_status_text = med.expiry_status()
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

    return render(request, 'inventory/medicine_sell.html', {'medicine': medicine, 'error': error})

# ----- SALES LIST VIEW -----
@login_required
def sales_list(request):
    query = request.GET.get('q', '')
    sales = Sale.objects.select_related('medicine').all().order_by('-id')
    if query:
        sales = sales.filter(medicine__name__icontains=query)

    today = timezone.now().date()
    daily_sales = sales.filter(sale_date__date=today)

    # Add calculated fields
    for sale in sales:
        sale.profit = (sale.medicine.selling_price - sale.medicine.buying_price) * sale.quantity_sold
        sale.total_sale = sale.medicine.selling_price * sale.quantity_sold

    daily_total_profit = sum((s.medicine.selling_price - s.medicine.buying_price) * s.quantity_sold for s in daily_sales)
    daily_total_sales = sum(s.medicine.selling_price * s.quantity_sold for s in daily_sales)
    daily_total_items_sold = sum(s.quantity_sold for s in daily_sales)
    total_profit = sum(sale.profit for sale in sales)

    context = {
        'sales': sales,
        'total_profit': total_profit,
        'daily_total_profit': daily_total_profit,
        'daily_total_sales': daily_total_sales,
        'daily_total_items_sold': daily_total_items_sold,
        'query': query,
    }
    return render(request, 'inventory/sales_list.html', context)
