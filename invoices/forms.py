# invoices/forms.py
from django import forms
from .models import Invoice, InvoiceItem

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['date', 'due_date', 'tax_percentage']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'}), 'due_date': forms.DateInput(attrs={'type': 'date'})}

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity_type', 'quantity', 'unit_price']

InvoiceItemFormSet = forms.inlineformset_factory(Invoice, InvoiceItem, form=InvoiceItemForm, extra=1, can_delete=True)

class InvoiceStatusForm(forms.ModelForm):
    """A simple form to update only the status of an invoice."""
    class Meta:
        model = Invoice
        fields = ['status']