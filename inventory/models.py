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
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity_sold = models.PositiveIntegerField()
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity_sold} units of {self.medicine.name}"

    def profit(self):
        return (self.medicine.selling_price - self.medicine.buying_price) * self.quantity_sold