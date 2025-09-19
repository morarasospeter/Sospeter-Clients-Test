from django.db import models
from django.utils import timezone
from datetime import timedelta

# ----- MEDICINE CATEGORIES -----
CATEGORY_CHOICES = [
    ('Pain Relief & Anti-inflammatory', 'Pain Relief & Anti-inflammatory'),
    ('Antibiotics', 'Antibiotics'),
    ('Cold & Flu', 'Cold & Flu'),
    ('Stomach & Digestive', 'Stomach & Digestive'),
    ('Blood Pressure & Heart', 'Blood Pressure & Heart'),
    ('Diabetes', 'Diabetes'),
    ('Vitamins & Supplements', 'Vitamins & Supplements'),
    ("Women's Health", "Women's Health"),
    ('Topical/External', 'Topical/External'),
]

# ----- MEDICINE MODEL -----
class Medicine(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='Pain Relief & Anti-inflammatory'
    )
    quantity = models.PositiveIntegerField()
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    manufacturer = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def profit_per_unit(self):
        """Returns profit per unit of medicine"""
        return self.selling_price - self.buying_price

    def stock_status(self):
        """Returns stock status text"""
        if self.quantity <= 20:
            return "Low Stock"
        return "In Stock"

    def expiry_status(self):
        """Returns expiry status text"""
        if self.expiry_date <= timezone.now().date() + timedelta(days=30):
            return "Expiring Soon"
        return "Valid"

# ----- SALE MODEL -----
class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Mobile', 'Mobile Payment'),
    ]

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity_sold = models.PositiveIntegerField()
    sale_date = models.DateTimeField(auto_now_add=True)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='Cash')

    def __str__(self):
        return f"{self.quantity_sold} units of {self.medicine.name}"

    def profit(self):
        """Returns total profit for this sale"""
        return (self.medicine.selling_price - self.medicine.buying_price) * self.quantity_sold

    def total_sale(self):
        """Returns total sale value"""
        return self.medicine.selling_price * self.quantity_sold