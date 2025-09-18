from django.db import models

class Medicine(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)  # new
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)  # new
    expiry_date = models.DateField()
    manufacturer = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def profit_per_unit(self):
        return self.selling_price - self.buying_price
