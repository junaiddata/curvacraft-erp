# accounts/forms.py
from django import forms
from .models import Payment, CreditNote

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'date_paid', 'payment_method', 'notes']
        widgets = {'date_paid': forms.DateInput(attrs={'type': 'date'})}

class CreditNoteForm(forms.ModelForm):
    class Meta:
        model = CreditNote
        fields = ['amount', 'date_issued', 'reason']
        widgets = {'date_issued': forms.DateInput(attrs={'type': 'date'})}