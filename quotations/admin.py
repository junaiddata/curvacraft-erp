# quotations/admin.py

from django.contrib import admin
from .models import Quotation, QuotationItem

class QuotationItemInline(admin.TabularInline):
    """
    Allows editing of QuotationItem models directly within the Quotation admin page.
    """
    model = QuotationItem
    extra = 1 # Show 1 extra empty form by default
    fields = ('section', 'description', 'quantity', 'unit', 'unit_price')
    readonly_fields = ('total_amount',) # Display the calculated total but don't allow editing

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('quotation_number', 'enquiry', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('quotation_number', 'enquiry__customer__name')
    
    # This is the magic line!
    inlines = [QuotationItemInline]