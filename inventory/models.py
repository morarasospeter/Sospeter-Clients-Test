from django.db import models


class Medicine(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    manufacturer = models.CharField(max_length=100)

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

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity_sold = models.PositiveIntegerField()
    sale_date = models.DateTimeField(auto_now_add=True)
    payment_mode = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default='Cash'
    )

    def __str__(self):
        return f"{self.quantity_sold} units of {self.medicine.name}"

    def profit(self):
        return (self.medicine.selling_price - self.medicine.buying_price) * self.quantity_sold
