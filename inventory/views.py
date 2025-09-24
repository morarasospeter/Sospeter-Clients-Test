from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from .models import Medicine, Sale, SaleItem, Category
from .forms import MedicineForm
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse, HttpResponse
import json

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

# ----- MEDICINE LIST VIEW -----
@login_required
def medicine_list(request):
    query = request.GET.get('q')
    if query:
        medicines = Medicine.objects.filter(
            Q(name__icontains=query) | Q(manufacturer__icontains=query)
        ).order_by('name')
        categories = None
    else:
        medicines = Medicine.objects.all().order_by('name')
        categories = Category.objects.prefetch_related('medicines').all()

    low_stock = medicines.filter(quantity__lt=10)
    today_plus_30 = timezone.now().date() + timedelta(days=30)
    soon_to_expire = medicines.filter(expiry_date__lte=today_plus_30)

    for med in medicines:
        med.total_value = med.quantity * med.buying_price
        med.profit_per_unit_value = med.selling_price - med.buying_price

    total_quantity = sum(m.quantity for m in medicines)
    total_stock_value = sum(m.total_value for m in medicines)
    normal_stock_count = medicines.count() - low_stock.count()

    context = {
        'medicines': medicines,
        'categories': categories,
        'low_stock': low_stock,
        'soon_to_expire': soon_to_expire,
        'medicine_count': medicines.count(),
        'normal_stock_count': normal_stock_count,
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
    categories = Category.objects.all()
    return render(request, 'inventory/medicine_form.html', {'form': form, 'categories': categories})

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
    categories = Category.objects.all()
    return render(request, 'inventory/medicine_form.html', {'form': form, 'categories': categories})

# ----- MEDICINE DELETE -----
@login_required
def medicine_delete(request, id):
    medicine = get_object_or_404(Medicine, id=id)
    if request.method == 'POST':
        medicine.delete()
        return redirect('medicine_list')
    return render(request, 'inventory/medicine_delete.html', {'medicine': medicine})

# ----- MEDICINE SELL (MULTIPLE OR SINGLE) -----
@login_required
def medicine_sell(request, medicine_id=None):
    query = request.GET.get('q')
    error = None
    preselected_medicine = None

    if medicine_id:
        preselected_medicine = get_object_or_404(Medicine, id=medicine_id)

    if query:
        medicines = Medicine.objects.filter(
            Q(name__icontains=query) | Q(manufacturer__icontains=query)
        ).order_by('name')
    else:
        medicines = Medicine.objects.all().order_by('name')

    if request.method == 'POST':
        items_data = json.loads(request.POST.get('items', '[]'))
        payment_mode = request.POST.get('payment_mode', 'Cash')

        # Single medicine sale
        if not items_data and preselected_medicine:
            qty = int(request.POST.get('quantity', 0))
            if qty <= 0 or qty > preselected_medicine.quantity:
                error = f"Invalid quantity for {preselected_medicine.name}"
            else:
                sale = Sale.objects.create(payment_mode=payment_mode)
                SaleItem.objects.create(
                    sale=sale,
                    medicine=preselected_medicine,
                    quantity=qty,
                    price=preselected_medicine.selling_price
                )
                sale.total_amount = qty * preselected_medicine.selling_price
                sale.save()
                return redirect('sale_receipt', sale_id=sale.id)

        # Multiple medicine sale
        elif items_data:
            sale = Sale.objects.create(payment_mode=payment_mode)
            total_amount = 0
            for item in items_data:
                try:
                    med = Medicine.objects.get(id=item['medicine_id'])
                    qty = int(item['quantity'])
                    price = float(item['price'])
                    if qty <= 0 or qty > med.quantity:
                        raise ValueError(f"Invalid quantity for {med.name}")
                    SaleItem.objects.create(
                        sale=sale,
                        medicine=med,
                        quantity=qty,
                        price=price
                    )
                    total_amount += price * qty
                except Exception as e:
                    sale.delete()
                    error = str(e)
                    return render(request, 'inventory/medicine_sell_multiple.html', {
                        'medicines': medicines,
                        'error': error,
                        'query': query,
                        'preselected_medicine': preselected_medicine
                    })
            sale.total_amount = total_amount
            sale.save()
            return redirect('sale_receipt', sale_id=sale.id)
        else:
            error = "No medicines selected for sale."

    context = {
        'medicines': medicines,
        'preselected_medicine': preselected_medicine,
        'error': error,
        'query': query,
    }
    return render(request, 'inventory/medicine_sell_multiple.html', context)

# ----- SALES LIST VIEW -----
@login_required
def sales_list(request):
    query = request.GET.get('q')
    sales = Sale.objects.prefetch_related('items__medicine').all().order_by('-id')

    if query:
        sales = sales.filter(items__medicine__name__icontains=query).distinct()

    sales_data = []
    total_profit = 0
    today = timezone.now().date()
    todays_sales_data = []

    for sale in sales:
        sale_total = sum(item.price * item.quantity for item in sale.items.all())
        sale_profit = sum((item.price - item.medicine.buying_price) * item.quantity for item in sale.items.all())
        items_info = [{
            'name': item.medicine.name,
            'quantity': item.quantity,
            'price': item.price,
            'subtotal': item.price * item.quantity
        } for item in sale.items.all()]
        sales_data.append({
            'sale': sale,
            'total_sale': sale_total,
            'profit': sale_profit,
            'items_info': items_info
        })
        total_profit += sale_profit
        if sale.sale_date.date() == today:
            todays_sales_data.append({
                'sale': sale,
                'total_sale': sale_total,
                'profit': sale_profit,
                'items_info': items_info
            })

    todays_total_sales = sum(item['total_sale'] for item in todays_sales_data)
    todays_total_profit = sum(item['profit'] for item in todays_sales_data)

    context = {
        'sales_data': sales_data,
        'total_profit': total_profit,
        'todays_sales_data': todays_sales_data,
        'todays_total_sales': todays_total_sales,
        'todays_total_profit': todays_total_profit,
        'query': query,
    }
    return render(request, 'inventory/sales_list.html', context)

# ----- SALE RECEIPT VIEW (Updated) -----
@login_required
def sale_receipt(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    # Calculate total per medicine and grand total
    sale_items = sale.items.all()
    for item in sale_items:
        item.total = item.quantity * item.price  # total per medicine

    total_price = sum(item.total for item in sale_items)
    profit = sum((item.price - item.medicine.buying_price) * item.quantity for item in sale_items)

    # Plain text download
    if request.GET.get("print") == "true":
        receipt_text = "--- PHARMACY RECEIPT ---\n\n"
        for item in sale_items:
            receipt_text += f"{item.medicine.name} - {item.quantity} x {item.price} = {item.total}\n"
        receipt_text += f"\nTotal Price: {total_price}\nPayment Mode: {sale.payment_mode}\nDate: {sale.sale_date.strftime('%Y-%m-%d %H:%M')}\n\n-------------------------\nThank you for shopping with us!"
        response = HttpResponse(receipt_text, content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="receipt.txt"'
        return response

    # Render HTML receipt with buttons
    context = {
        'sale': sale,
        'total_price': total_price,
        'profit': profit,
        'sale_items': sale_items,  # pass items with total
        'show_back_button': False
    }
    return render(request, 'inventory/sale_receipt.html', context)

# ----- SALE DELETE VIEW -----
@login_required
def sale_delete(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    for item in sale.items.all():
        item.medicine.quantity += item.quantity
        item.medicine.save()
    sale.delete()
    return redirect('sales_list')
