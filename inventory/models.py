from django.db import models

# Add medicine categories
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

class Medicine(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)  # New category field
    quantity = models.PositiveIntegerField()
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    manufacturer = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def profit_per_unit(self):
        return self.selling_price - self.buying_price

    def stock_status(self):
        if self.quantity <= 20:  # Example threshold for low stock
            return "Low Stock"  # Updated text here
        return "In Stock"

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
        return (self.medicine.selling_price - self.medicine.buying_price) * self.quantity_sold