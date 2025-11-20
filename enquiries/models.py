# enquiries/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _

class Customer(models.Model):
    """Stores customer information."""
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Enquiry(models.Model):
    """Stores all details related to a new client enquiry."""

    class ProjectType(models.TextChoices):
        DESIGN = 'DESIGN', _('Design')
        FITOUT = 'FITOUT', _('Fitout')
        BOTH = 'BOTH', _('Both')
    
    class EnquiryStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        QUALIFIED = 'QUALIFIED', _('Qualified') # Means ready for quotation
        REJECTED = 'REJECTED', _('Rejected')

    # Linking to the customer
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='enquiries')

    # Enquiry Details
    project_type = models.CharField(max_length=10, choices=ProjectType.choices)
    scope = models.TextField()
    location = models.CharField(max_length=255)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    timeframe = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=EnquiryStatus.choices, default=EnquiryStatus.PENDING)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Enquiry for {self.customer.name} - {self.location}"