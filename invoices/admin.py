from django.contrib import admin
from .models import Invoice

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):    
    list_display = ('invoice_number', 'project', 'status', 'created_at')
    search_fields = ('invoice_number', 'project__name')
    list_filter = ('status', 'created_at')