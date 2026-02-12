# accounts/forms.py
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Payment, CreditNote


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'date_paid', 'payment_method', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'type': 'number',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
                'class': 'form-input-amount',
                'inputmode': 'decimal',
            }),
            'date_paid': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
            }),
            'payment_method': forms.TextInput(attrs={
                'placeholder': 'e.g., Bank Transfer, Cheque, Cash',
                'class': 'form-input',
                'list': 'payment-methods',
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Optional notes about this payment',
                'class': 'form-input',
            }),
        }
        help_texts = {
            'amount': 'Enter the payment amount in AED (max 2 decimal places).',
            'payment_method': 'How was this payment received?',
        }

    def __init__(self, *args, max_amount=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Round to 2 decimals for comparison - allows 10.12 when amount_due is 10.115
        self.max_amount_rounded = (
            Decimal(str(round(float(max_amount), 2))) if max_amount is not None else None
        )
        if max_amount is not None:
            self.fields['amount'].widget.attrs['max'] = str(float(self.max_amount_rounded))
            self.fields['amount'].help_text = f'Amount due: AED {self.max_amount_rounded:,.2f} (max 2 decimal places).'

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None:
            return amount
        if amount <= 0:
            raise ValidationError('Payment amount must be greater than zero.')
        if self.max_amount_rounded is not None and amount > self.max_amount_rounded:
            raise ValidationError(
                f'Payment amount cannot exceed AED {self.max_amount_rounded:,.2f} (amount due).'
            )
        # Enforce 2 decimal places
        return Decimal(str(round(float(amount), 2)))

class CreditNoteForm(forms.ModelForm):
    class Meta:
        model = CreditNote
        fields = ['amount', 'date_issued', 'reason']
        widgets = {'date_issued': forms.DateInput(attrs={'type': 'date'})}