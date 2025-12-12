# reports/models.py
from django.db import models
from django.utils import timezone
from projects.models import Project

class DailyReport(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='daily_reports')
    report_number = models.PositiveIntegerField(blank=True)
    date = models.DateField(default=timezone.now)
    contractor_name = models.CharField(max_length=255, blank=True)
    subcontractor_name = models.CharField(max_length=255, blank=True, verbose_name="Subcontractor Name")
    chronological_account = models.TextField(blank=True, help_text="8:00 AM to 6:00 PM - Describe the work done.")
    activities_for_next_day = models.TextField(blank=True)
    issues_encountered = models.TextField(blank=True, verbose_name="Force Work / Changes Encountered / Safety Issues")
    
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('project', 'date')
        ordering = ['-date']

    def save(self, *args, **kwargs):
        # Auto-increment report_number scoped to the project
        if not self.pk: # Only on creation
            last_report = DailyReport.objects.filter(project=self.project).order_by('report_number').last()
            self.report_number = (last_report.report_number + 1) if last_report else 1
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"DPR #{self.report_number} for {self.project.title}"

class ManpowerLog(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='manpower_logs')
    staff_type = models.CharField(max_length=100, verbose_name="Staffs & Labor")
    day_count = models.PositiveIntegerField(default=0, verbose_name="Day")
    night_count = models.PositiveIntegerField(default=0, verbose_name="Night")

class SubcontractorLog(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='subcontractor_logs')
    staff_type = models.CharField(max_length=100, verbose_name="Staffs & Labor")
    day_count = models.PositiveIntegerField(default=0, verbose_name="Day")
    night_count = models.PositiveIntegerField(default=0, verbose_name="Night")

class EquipmentLog(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='equipment_logs')
    equipment_name = models.CharField(max_length=100, verbose_name="Equipment")
    day_count = models.PositiveIntegerField(default=0, verbose_name="Day")
    night_count = models.PositiveIntegerField(default=0, verbose_name="Night")