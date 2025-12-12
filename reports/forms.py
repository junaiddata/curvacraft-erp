# reports/forms.py
from django import forms
from .models import DailyReport, ManpowerLog, SubcontractorLog, EquipmentLog

class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        # Add 'contractor_name' to this list
        fields = ['date', 'contractor_name', 'subcontractor_name','chronological_account', 'activities_for_next_day', 'issues_encountered']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

# Create the formsets for the line items
ManpowerLogFormSet = forms.inlineformset_factory(
    DailyReport, ManpowerLog, fields=('staff_type', 'day_count', 'night_count'),
    extra=1, can_delete=True
)
SubcontractorLogFormSet = forms.inlineformset_factory(
    DailyReport, SubcontractorLog, fields=('staff_type', 'day_count', 'night_count'),
    extra=1, can_delete=True
)
EquipmentLogFormSet = forms.inlineformset_factory(
    DailyReport, EquipmentLog, fields=('equipment_name', 'day_count', 'night_count'),
    extra=1, can_delete=True
)