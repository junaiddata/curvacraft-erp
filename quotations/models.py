# quotations/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from enquiries.models import Enquiry
from decimal import Decimal
from django.utils import timezone # Import the timezone module
class Quotation(models.Model):
    """
    Represents the main quotation document linked to an enquiry.
    """
    class QuotationStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SENT = 'SENT', _('Sent')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        REJECTED = 'REJECTED', _('Rejected')
        # --- NEW FIELD: Define the type of this quotation ---
    class QuoteType(models.TextChoices):
        DESIGN = 'DESIGN', _('Design')
        FITOUT = 'FITOUT', _('Fitout')

    # Link to the original enquiry
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE, related_name='quotations')

    quote_type = models.CharField(max_length=10, choices=QuoteType.choices)
    quotation_number = models.CharField(max_length=50, unique=True,blank=True)
    status = models.CharField(max_length=10, choices=QuotationStatus.choices, default=QuotationStatus.PENDING)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensure an enquiry can have only one of each type of quote
        unique_together = ('enquiry', 'quote_type')
    # --- NEW METHOD: Overriding save() for automatic numbering ---
    def save(self, *args, **kwargs):
        # We only generate a number if the object is being created for the first time
        # and doesn't already have a number.
        if not self.quotation_number:
            # Get the current year's last two digits (e.g., '25' for 2025)
            current_year_short = f"{timezone.now():%y}"
            prefix = f'CURV-QT-{current_year_short}'

            # Find the last quotation from the current year
            last_quotation = Quotation.objects.filter(
                quotation_number__startswith=prefix
            ).order_by('quotation_number').last()

            if last_quotation:
                # If one exists, extract its sequence number, increment it
                last_sequence = int(last_quotation.quotation_number[-5:])
                new_sequence = last_sequence + 1
            else:
                # If this is the first one of the year, start the sequence at 1
                new_sequence = 1
            
            # Format the new number and assign it
            self.quotation_number = f'{prefix}{new_sequence:05d}'
            
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
        return f"{self.get_quote_type_display()} Quote for {self.enquiry.customer.name}"

class QuotationItem(models.Model):
    """
    Represents a single line item within a quotation.
    This is where we add the description, quantity, price, etc.
    """

    # Link to the parent quotation
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')

    # Item Details
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, help_text="e.g., M2, Pcs, Lump Sum") # Free text input for unit
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_amount(self):
        """Calculates the total for this line item."""
        return Decimal(self.quantity) * Decimal(self.unit_price)
    


    def __str__(self):
        return f"Item for {self.quotation.quotation_number}"