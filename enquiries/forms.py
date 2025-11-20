# enquiries/forms.py

from django import forms
from .models import Enquiry, Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone_number', 'address']

class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['project_type', 'scope', 'location', 'budget', 'timeframe', 'status']


class EnquiryStatusForm(forms.ModelForm):
    """A simple form to update only the status of an enquiry."""
    class Meta:
        model = Enquiry
        fields = ['status']