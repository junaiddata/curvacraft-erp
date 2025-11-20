# progress/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from projects.models import Project
from users.models import User

# We need a function to define the upload path for files
def progress_file_upload_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/project_<id>/<date>_<filename>
    return f'project_{instance.project.id}/{instance.date}_{filename}'

class DailyProgress(models.Model):
    """
    A single entry that tracks the planned task, the actual progress,
    and admin remarks for a specific day of a project.
    """
    class ProgressStatus(models.TextChoices):
        PENDING_SUBMISSION = 'PENDING', _('Pending Submission') # Task set, SCO to submit
        SUBMITTED = 'SUBMITTED', _('Submitted for Review') # SCO submitted, Admin to review
        REVIEWED = 'REVIEWED', _('Reviewed and Closed') # Admin reviewed, record is locked

    # Core Links
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='progress_reports')
    date = models.DateField()

    # --- NEW FIELD: Assign task to a specific SCO ---
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE, # If the user is deleted, their tasks are also deleted.
        related_name='daily_tasks',
        limit_choices_to={'role': 'sco'},
        help_text="The SCO this specific task is assigned to.",
        

    )

    # --- Fields for the Admin ---
    planned_task = models.TextField(help_text="Admin: Enter the tasks for the day here.")
    admin_remarks = models.TextField(blank=True, help_text="Admin: Enter your remarks after SCO submission.")

    # --- Fields for the SCO ---
    actual_progress = models.TextField(blank=True, help_text="SCO: Describe the actual work done.")
    file_upload = models.FileField(upload_to=progress_file_upload_path, blank=True, null=True, help_text="SCO: Upload any relevant files or photos.")

    # --- Status and Tracking ---
    status = models.CharField(max_length=20, choices=ProgressStatus.choices, default=ProgressStatus.PENDING_SUBMISSION)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_progress')

    class Meta:
        # UPDATED: A task is now unique for a project, a date, AND an assigned SCO.
        ordering = ['-date']
        unique_together = ('project', 'date', 'assigned_to')

    def __str__(self):
        return f"Progress for {self.project.title} on {self.date} ({self.assigned_to.username})"
    


# Helper function for weekly file uploads
def weekly_progress_file_upload_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/project_<id>/weekly_<date>_<filename>
    return f'project_{instance.project.id}/weekly_{instance.week_start_date}_{filename}'

class WeeklyProgress(models.Model):
    """
    Tracks the planned task, actual progress, and admin remarks for a
    specific week of a project.
    """
    # We can reuse the same status choices
    ProgressStatus = DailyProgress.ProgressStatus

    # Core Links
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='weekly_reports')
    week_start_date = models.DateField(help_text="Select the Monday of the week for this report.")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='weekly_tasks',
        limit_choices_to={'role': 'sco'},
        help_text="Assign to a specific SCO, or leave blank for a general weekly report.",
    )

    # Fields for the Admin
    planned_task = models.TextField(help_text="Admin: Enter the main goals for the week.")
    admin_remarks = models.TextField(blank=True, help_text="Admin: Enter your review for the week.")

    # Fields for the SCO Team
    actual_progress = models.TextField(blank=True, help_text="SCO: Summarize the work done this week.")
    file_upload = models.FileField(upload_to=weekly_progress_file_upload_path, blank=True, null=True)

    # Status and Tracking
    status = models.CharField(max_length=20, choices=ProgressStatus.choices, default=ProgressStatus.PENDING_SUBMISSION)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_weekly_progress')

    class Meta:
        ordering = ['-week_start_date']
        unique_together = ('project', 'week_start_date', 'assigned_to')
        # A project can only have one report per week_start_date
        

    def __str__(self):
        return f"Weekly Report for {self.project.title} starting {self.week_start_date}"