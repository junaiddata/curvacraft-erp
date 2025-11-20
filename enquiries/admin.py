# enquiries/admin.py

from django.contrib import admin
from .models import Customer, Enquiry

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number')
    search_fields = ('name', 'email')

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('customer', 'project_type', 'location', 'status', 'created_at')
    list_filter = ('status', 'project_type', 'created_at')
    search_fields = ('customer__name', 'location')
    date_hierarchy = 'created_at'