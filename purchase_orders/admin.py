# purchase_orders/admin.py

from django.contrib import admin
from .models import Contractor, PurchaseOrder, PurchaseOrderItem, PurchaseOrderDocument

class PurchaseOrderItemInline(admin.TabularInline):
    """
    Allows editing of PurchaseOrderItem models directly within the PurchaseOrder admin page.
    """
    model = PurchaseOrderItem
    extra = 1
    fields = ('description', 'quantity', 'unit', 'unit_price')
    readonly_fields = ('total_amount',)

class PurchaseOrderDocumentInline(admin.TabularInline):
    """
    Allows viewing/managing documents within the PurchaseOrder admin page.
    """
    model = PurchaseOrderDocument
    extra = 0
    fields = ('file', 'description', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'contact_person', 'email', 'phone_number')
    ordering = ('name',)

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'contractor', 'status', 'grand_total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('po_number', 'contractor__name')
    readonly_fields = ('po_number', 'created_at', 'updated_at')
    inlines = [PurchaseOrderItemInline, PurchaseOrderDocumentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('po_number', 'contractor', 'status')
        }),
        ('Financial', {
            'fields': ('tax_percentage',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PurchaseOrderDocument)
class PurchaseOrderDocumentAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'description', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('purchase_order__po_number', 'description')
    readonly_fields = ('uploaded_at',)
