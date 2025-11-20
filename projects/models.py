# projects/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from quotations.models import Quotation
from users.models import User # Import our custom User model
from decimal import Decimal
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
    def total_invoiced(self):
        # Sum the grand_total of all invoices that are NOT void
        return sum(inv.grand_total for inv in self.invoices.exclude(status='VOID'))

    @property
    def amount_pending(self):
        return self.grand_total - self.total_invoiced
    

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