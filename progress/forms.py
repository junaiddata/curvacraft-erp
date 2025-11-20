# progress/forms.py

from django import forms
from .models import DailyProgress, User,WeeklyProgress

class DailyTaskCreationForm(forms.ModelForm):
    # We define the field here to customize it
    assigned_to = forms.ModelChoiceField(queryset=User.objects.none(),required=False )

    class Meta:
        model = DailyProgress
        # Add 'assigned_to' to the fields list
        fields = ['date', 'assigned_to', 'planned_task']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'date': 'Task Date',
            'assigned_to': 'Assign to SCO',
            'planned_task': 'Task to be Done'
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['assigned_to'].queryset = project.assigned_scos.all()
            # Set a nice empty label
            self.fields['assigned_to'].empty_label = "All Assigned SCOs"

class SCOProgressUpdateForm(forms.ModelForm):
    class Meta:
        model = DailyProgress
        fields = ['actual_progress', 'file_upload']
        widgets = {
            'actual_progress': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'actual_progress': 'Describe the work you completed',
            'file_upload': 'Upload a supporting file or photo (optional)',
        }

# --- THIS IS THE MISSING FORM ---
class AdminReviewForm(forms.ModelForm):
    class Meta:
        model = DailyProgress
        # We only need the remarks field. The status change will be handled in the view.
        fields = ['admin_remarks']
        widgets = {
            'admin_remarks': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add your remarks here...'}),
        }
        labels = {
            'admin_remarks': 'Your Remarks',
        }


class WeeklyTaskCreationForm(forms.ModelForm):
    # Add the dynamic field
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False
    )

    class Meta:
        model = WeeklyProgress
        # Add 'assigned_to' to the fields
        fields = ['week_start_date', 'assigned_to', 'planned_task']
        widgets = { 'week_start_date': forms.DateInput(attrs={'type': 'date'}) }
        labels = {
            'week_start_date': 'Week Starting On (will default to Monday)',
            'assigned_to': 'Assign to SCO',
            'planned_task': 'Weekly Goals / Planned Tasks'
        }

    # Add the dynamic queryset logic
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['assigned_to'].queryset = project.assigned_scos.all()
            self.fields['assigned_to'].empty_label = "All Assigned SCOs"

            
class SCOWeeklyUpdateForm(forms.ModelForm):
    class Meta:
        model = WeeklyProgress
        fields = ['actual_progress', 'file_upload']
        labels = {
            'actual_progress': 'Summary of work completed this week',
            'file_upload': 'Upload a summary document or photo (optional)',
        }

class AdminWeeklyReviewForm(forms.ModelForm):
    class Meta:
        model = WeeklyProgress
        fields = ['admin_remarks']
        labels = { 'admin_remarks': 'Your Weekly Review Remarks' }