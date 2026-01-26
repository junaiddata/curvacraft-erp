# purchase_orders/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.utils import timezone

# Helper function for PO document uploads
def po_document_upload_path(instance, filename):
    """File will be uploaded to MEDIA_ROOT/po_{po_id}/{filename}"""
    return f'po_{instance.purchase_order.id}/{filename}'

class Contractor(models.Model):
    """
    Represents a contractor/vendor that receives purchase orders.
    """
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):
    """
    Represents a purchase order given to a contractor.
    """
    class POStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SENT = 'SENT', _('Sent')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        REJECTED = 'REJECTED', _('Rejected')
        COMPLETED = 'COMPLETED', _('Completed')

    contractor = models.ForeignKey(Contractor, on_delete=models.CASCADE, related_name='purchase_orders')
    po_number = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=10, choices=POStatus.choices, default=POStatus.PENDING)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Auto-generate PO number if not set."""
        if not self.po_number:
            # Get the current year's last two digits (e.g., '25' for 2025)
            current_year_short = f"{timezone.now():%y}"
            prefix = f'CURV-PO-{current_year_short}'

            # Find the last PO from the current year
            last_po = PurchaseOrder.objects.filter(
                po_number__startswith=prefix
            ).order_by('po_number').last()

            if last_po:
                # If one exists, extract its sequence number, increment it
                last_sequence = int(last_po.po_number[-5:])
                new_sequence = last_sequence + 1
            else:
                # If this is the first one of the year, start the sequence at 1
                new_sequence = 1
            
            # Format the new number and assign it
            self.po_number = f'{prefix}{new_sequence:05d}'
            
        # Call the original save() method to save the object to the database
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        """Calculates the sum of all line item totals."""
        return sum(item.total_amount for item in self.items.all())

    @property
    def tax_amount(self):
        """Calculates the amount of tax based on the subtotal."""
        if self.tax_percentage > 0:
            return (self.subtotal * self.tax_percentage) / 100
        return Decimal(0)
    
    @property
    def grand_total(self):
        """Calculates the final total including tax."""
        return self.subtotal + self.tax_amount

    def __str__(self):
        return f"PO {self.po_number} - {self.contractor.name}"

class PurchaseOrderItem(models.Model):
    """
    Represents a single line item within a purchase order.
    """
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    
    # Item Details
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, help_text="e.g., M2, Pcs, Lump Sum")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_amount(self):
        """Calculates the total for this line item."""
        return Decimal(self.quantity) * Decimal(self.unit_price)

    def __str__(self):
        return f"Item for {self.purchase_order.po_number}"

class PurchaseOrderDocument(models.Model):
    """
    Represents a document/file attached to a purchase order.
    Allows multiple files to be uploaded per PO.
    """
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=po_document_upload_path)
    description = models.CharField(max_length=200, blank=True, help_text="Optional description of the document")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Document for {self.purchase_order.po_number} - {self.description or self.file.name}"
