# projects/forms.py

from django import forms
from .models import Project ,ProjectItem # Add ProjectItem

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        # We only need the user to set the title and assign SCOs.
        # The 'quotation' will be set automatically.
        fields = ['title', 'status', 'assigned_scos']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use the better widget for ManyToMany fields
        self.fields['assigned_scos'].widget = forms.CheckboxSelectMultiple()
        # We can also limit the queryset again here if we want to be extra safe
        self.fields['assigned_scos'].queryset = self.fields['assigned_scos'].queryset.filter(role='sco')

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

ProjectItemFormSet = forms.inlineformset_factory(
    Project, ProjectItem, form=ProjectItemForm,
    extra=0, # We start with 0 extra, as they are copied from the quote
    can_delete=True
)