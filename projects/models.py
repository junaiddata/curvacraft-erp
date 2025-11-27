# projects/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from quotations.models import Quotation
from users.models import User # Import our custom User model
from decimal import Decimal
from django.db.models import Sum


class Project(models.Model):
    """
    Represents an active project, created from an accepted quotation.
    """
    class ProjectStatus(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', _('Not Started')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        ON_HOLD = 'ON_HOLD', _('On Hold')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    # Link to the quotation that this project was created from
    quotation = models.OneToOneField(Quotation, on_delete=models.PROTECT, related_name='project')
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    # --- Key Feature: Assigning an SCO ---
    # We link to the User model, but only want to show SCOs as options.
    assigned_scos = models.ManyToManyField(
        User,
        related_name='projects',
        limit_choices_to={'role': 'sco'},
        blank=True, # This field can be empty
        help_text="Assign one or more Site Coordination Officers to this project."
    )

    # Project Details
    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.NOT_STARTED
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Helper properties to easily access related data
    @property
    def customer(self):
        return self.quotation.enquiry.customer

    @property
    def location(self):
        return self.quotation.enquiry.location

    def __str__(self):
        return self.title
    
    @property
    def subtotal(self):
        # Note: it now sums 'project_items', not 'quotation.items'
        return sum(item.total_amount for item in self.project_items.all())

    @property
    def tax_amount(self):
        if self.tax_percentage > 0:
            return (self.subtotal * self.tax_percentage) / 100
        return Decimal(0)

    @property
    def grand_total(self):
        return self.subtotal + self.tax_amount
    
    @property
    def total_invoiced_subtotal(self):
        """Calculates the SUM of the SUBTOTALS (pre-VAT) of all non-voided invoices."""
        valid_invoices = self.invoices.exclude(status='VOID')
        return sum(inv.subtotal for inv in valid_invoices) or Decimal(0)

    @property
    def budget_remaining_to_invoice_subtotal(self):
        """
        Calculates the pre-VAT value of the project that has not yet been invoiced.
        This is the most important metric for project management.
        """
        # Compares VAT-exclusive with VAT-exclusive
        return self.subtotal - self.total_invoiced_subtotal

    @property
    def budget_remaining_to_invoice_grand(self):
        """
        Calculates the VAT-inclusive value of the project that has not yet been invoiced.
        """
        # Compares VAT-inclusive with VAT-inclusive
        return self.grand_total - self.total_invoiced_grand

    @property
    def total_invoiced_grand(self):
        """Calculates the SUM of the GRAND TOTALS (incl. VAT) of all non-voided invoices."""
        valid_invoices = self.invoices.exclude(status='VOID')
        return sum(inv.grand_total for inv in valid_invoices) or Decimal(0)

    @property
    def total_received(self):
        """Calculates the total amount of actual money received across all payments."""
        total = self.invoices.exclude(status='VOID').aggregate(total=Sum('payments__amount'))['total']
        return total or Decimal(0)
        
    @property
    def total_credited(self):
        """Calculates the total amount credited across all credit notes."""
        total = self.invoices.exclude(status='VOID').aggregate(total=Sum('credit_notes__amount'))['total']
        return total or Decimal(0)

    @property
    def accounts_receivable(self):
        """
        THE CORRECT "AMOUNT PENDING". This is the actual cash you are waiting for.
        Calculated as: Total Billed (incl. VAT) - Total Payments Received - Total Credit Notes Issued.
        """
        # This is the corrected, final formula.
        return self.total_invoiced_grand - self.total_received - self.total_credited
    

# --- ADD THIS ENTIRE NEW MODEL ---
class ProjectItem(models.Model):
    """A single line item in the final project scope/budget."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_items')
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_amount(self):
        return Decimal(self.quantity) * Decimal(self.unit_price)

    def __str__(self):
        return self.description[:50]