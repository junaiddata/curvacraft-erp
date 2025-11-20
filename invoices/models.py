# invoices/models.py
from django.db import models
from django.utils import timezone
from decimal import Decimal
from projects.models import Project

class Invoice(models.Model):
    class InvoiceStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SENT = 'SENT', 'Sent'
        PAID = 'PAID', 'Paid'
        VOID = 'VOID', 'Void' # The "rewind" status

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField(default=timezone.now)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # --- Automatic Invoice Number Generation ---
        if not self.invoice_number:
            current_year = timezone.now().year
            last_invoice = Invoice.objects.filter(invoice_number__startswith=f'CURV-{current_year}').order_by('invoice_number').last()
            if last_invoice:
                last_seq = int(last_invoice.invoice_number[-3:])
                new_seq = last_seq + 1
            else:
                new_seq = 1
            self.invoice_number = f'CURV-{current_year}{new_seq:03d}'
        super().save(*args, **kwargs)

    # --- Calculation Properties ---
    @property
    def subtotal(self):
        return sum(item.total_amount for item in self.items.all())
    @property
    def tax_amount(self):
        return (self.subtotal * self.tax_percentage) / 100
    @property
    def grand_total(self):
        return self.subtotal + self.tax_amount

    def __str__(self):
        return self.invoice_number

class InvoiceItem(models.Model):
    class QuantityType(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', '%'
        FIXED = 'FIXED', 'Fixed Qty'

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.TextField()
    quantity_type = models.CharField(max_length=10, choices=QuantityType.choices, default=QuantityType.FIXED)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="For percentage, this is the project total. For fixed, it's the item price.")

    @property
    def total_amount(self):
        if self.quantity_type == self.QuantityType.PERCENTAGE:
            return (self.quantity / 100) * self.unit_price
        return self.quantity * self.unit_price