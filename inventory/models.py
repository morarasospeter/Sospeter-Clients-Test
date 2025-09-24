from django.db import models
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Medicine(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    manufacturer = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='medicines')

    def __str__(self):
        return self.name

    def profit_per_unit(self):
        return self.selling_price - self.buying_price


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Mobile', 'Mobile Payment'),
    ]

    sale_date = models.DateTimeField(auto_now_add=True)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='Cash')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Sale #{self.id} - {self.sale_date.strftime('%Y-%m-%d %H:%M')}"

    def calculate_total(self):
        total = sum(item.price * item.quantity for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=["total_amount"])
        return total


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.medicine.name}"

    def profit(self):
        return (self.price - self.medicine.buying_price) * self.quantity


# -----------------------------
# SIGNALS FOR STOCK MANAGEMENT
# -----------------------------

# 1. Capture old quantity BEFORE saving
@receiver(pre_save, sender=SaleItem)
def store_old_quantity(sender, instance, **kwargs):
    if instance.pk:  # means update
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_quantity = old_instance.quantity
        except sender.DoesNotExist:
            instance._old_quantity = 0
    else:  # new record
        instance._old_quantity = 0


# 2. Adjust stock AFTER saving
@receiver(post_save, sender=SaleItem)
def update_stock_on_save(sender, instance, created, **kwargs):
    medicine = instance.medicine
    if created:
        # subtract exactly what was sold
        medicine.quantity -= instance.quantity
    else:
        # adjust by the difference
        difference = instance.quantity - instance._old_quantity
        medicine.quantity -= difference
    medicine.save(update_fields=["quantity"])


# 3. Restore stock when sale item is deleted
@receiver(post_delete, sender=SaleItem)
def restore_stock_on_delete(sender, instance, **kwargs):
    medicine = instance.medicine
    medicine.quantity += instance.quantity
    medicine.save(update_fields=["quantity"])
