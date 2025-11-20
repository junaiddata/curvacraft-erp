# progress/admin.py

from django.contrib import admin
from .models import DailyProgress

@admin.register(DailyProgress)
class DailyProgressAdmin(admin.ModelAdmin):
    list_display = ('date', 'project', 'status', 'submitted_by')
    list_filter = ('status', 'project', 'date')
    search_fields = ('project__title', 'date')
    ordering = ('-date',)

    # Organize the fields for clarity
    fieldsets = (
        ("Day's Plan (Admin)", {
            'fields': ('project', 'date', 'planned_task')
        }),
        ("SCO's Report (SCO)", {
            'fields': ('actual_progress', 'file_upload', 'submitted_by')
        }),
        ("Admin's Review", {
            'fields': ('status', 'admin_remarks')
        }),
    )