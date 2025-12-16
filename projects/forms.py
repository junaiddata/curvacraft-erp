# projects/forms.py
from django import forms
from .models import Project, ProjectItem, MilestonePhase, MilestoneTask

# --- Project & ProjectItem Forms (These are correct) ---
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'location','status', 'mobilization_date', 'handover_date', 'assigned_scos']
        widgets = {
            'mobilization_date': forms.DateInput(attrs={'type': 'date'}),
            'handover_date': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_scos'].widget = forms.CheckboxSelectMultiple()
        self.fields['assigned_scos'].queryset = self.fields['assigned_scos'].queryset.filter(role='sco', is_active=True)

class ProjectItemForm(forms.ModelForm):
    class Meta:
        model = ProjectItem
        fields = ['description', 'quantity', 'unit', 'unit_price']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Item Description'}),
            'quantity': forms.NumberInput(attrs={'placeholder': 'e.g., 5'}),
            'unit': forms.TextInput(attrs={'placeholder': 'e.g., M2, Pcs'}),
            'unit_price': forms.NumberInput(attrs={'placeholder': 'e.g., 165.00'}),
        }

ProjectItemFormSet = forms.inlineformset_factory(Project, ProjectItem, form=ProjectItemForm, extra=0, can_delete=True)


# --- MILESTONE TRACKING FORMS (This is the corrected section) ---

class MilestoneTaskForm(forms.ModelForm):
    """This form is for a single task row."""
    class Meta:
        model = MilestoneTask
        fields = ['sl_no', 'description', 'timeline_date', 'invoices_submitted', 'amount_received_date']
        widgets = {
            'timeline_date': forms.DateInput(attrs={'type': 'date'}),
            'amount_received_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows':1, 'placeholder': 'Task description or Feedback...'}),
        }

# This is a formset for the tasks that belong TO A PHASE
MilestoneTaskFormSet = forms.inlineformset_factory(
    MilestonePhase,
    MilestoneTask,
    form=MilestoneTaskForm,
    extra=1,
    can_delete=True
    # The 'prefix' argument has been correctly removed from here
)

class MilestonePhaseForm(forms.ModelForm):
    """This form is for the main Phase header."""
    class Meta:
        model = MilestonePhase
        
        # --- THIS IS THE FIX ---
        # Change 'timeline' to 'default_timeline' to match the model
        fields = ['details', 'name', 'default_timeline']
        
        # widgets = {
        #     'details': forms.TextInput(attrs={'readonly': True, 'style': 'border:none; background:transparent;'}),
        #     'name': forms.TextInput(attrs={'readonly': True, 'style': 'border:none; background:transparent;'}),
        #     # The widget for 'default_timeline' will be a standard text input, which is what we want.
        # }

# This is a model formset for ALL the phases belonging to a project.
MilestonePhaseFormSet = forms.modelformset_factory(
    MilestonePhase,
    form=MilestonePhaseForm,
    extra=0,
    can_delete=False
)