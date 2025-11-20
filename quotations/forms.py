# quotations/forms.py
from django import forms
from .models import Quotation, QuotationItem

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['tax_percentage', 'status']

class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = ['description', 'quantity', 'unit', 'unit_price']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Item Description'}),
            'quantity': forms.NumberInput(attrs={'placeholder': 'e.g., 5'}),
            'unit': forms.TextInput(attrs={'placeholder': 'e.g., M2, Pcs'}),
            'unit_price': forms.NumberInput(attrs={'placeholder': 'e.g., 165.00'}),
        }

# We will use a formset for multiple items
QuotationItemFormSet = forms.inlineformset_factory(
    Quotation, QuotationItem, form=QuotationItemForm,
    extra=1, can_delete=True
)

class QuotationStatusForm(forms.ModelForm):
    """A simple form to update only the status of a quotation."""
    class Meta:
        model = Quotation
        fields = ['status']