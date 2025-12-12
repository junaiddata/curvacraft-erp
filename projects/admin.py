# projects/admin.py

from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    # CORRECT: Use the custom method 'display_scos'
    list_display = ('title', 'customer', 'location', 'status', 'display_scos')
    
    # CORRECT: We can't filter by a ManyToMany field directly in list_filter, so we remove it for now.
    list_filter = ('status',)
    
    # CORRECT: Search by the new field 'assigned_scos'
    search_fields = ('title', 'quotation__enquiry__customer__name', 'assigned_scos__username')
    
    readonly_fields = ('customer', 'location', 'created_at', 'updated_at')

    fieldsets = (
        ('Project Information', {
            'fields': ('title', 'status', 'quotation')
        }),
        ('Assignment', {
            # CORRECT: Use the new field 'assigned_scos'
            'fields': ('assigned_scos',)
        }),
        ('Derived Information', {
            'fields': ('customer', 'location')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    # This custom method is used in 'list_display' to show the SCOs
    def display_scos(self, obj):
        return ", ".join([sco.username for sco in obj.assigned_scos.all()])
    
    display_scos.short_description = 'Assigned SCOs'

