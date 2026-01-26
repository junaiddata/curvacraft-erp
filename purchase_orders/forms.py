# purchase_orders/forms.py

from django import forms
from .models import Contractor, PurchaseOrder, PurchaseOrderItem, PurchaseOrderDocument

class ContractorForm(forms.ModelForm):
    class Meta:
        model = Contractor
        fields = ['name', 'contact_person', 'email', 'phone_number', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Contractor Name'}),
            'contact_person': forms.TextInput(attrs={'placeholder': 'Contact Person Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Address'}),
        }

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['contractor', 'tax_percentage', 'status']
        widgets = {
            'contractor': forms.Select(attrs={'class': 'form-control'}),
            'tax_percentage': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '5.00'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['description', 'quantity', 'unit', 'unit_price']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Item Description'}),
            'quantity': forms.NumberInput(attrs={'placeholder': 'e.g., 5', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'placeholder': 'e.g., M2, Pcs'}),
            'unit_price': forms.NumberInput(attrs={'placeholder': 'e.g., 165.00', 'step': '0.01'}),
        }

# Inline formset for multiple items
PurchaseOrderItemFormSet = forms.inlineformset_factory(
    PurchaseOrder, PurchaseOrderItem, form=PurchaseOrderItemForm,
    extra=1, can_delete=True
)

class PurchaseOrderStatusForm(forms.ModelForm):
    """A simple form to update only the status of a purchase order."""
    class Meta:
        model = PurchaseOrder
        fields = ['status']

class PurchaseOrderDocumentForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderDocument
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'}),
            'description': forms.TextInput(attrs={'placeholder': 'Optional description'}),
        }
