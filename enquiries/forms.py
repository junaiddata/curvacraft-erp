# enquiries/forms.py

from django import forms
from .models import Enquiry, Customer

# enquiries/forms.py
from django import forms
from .models import Enquiry, Customer

class ExistingCustomerForm(forms.Form):
    """A form to select a customer that is already in the database."""
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all().order_by('name'),
        label="Select an Existing Customer"
    )

class CustomerForm(forms.ModelForm):
    """This is now the 'NewCustomerForm'."""
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone_number', 'address', 'trn_number']

class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['project_type', 'scope', 'location', 'budget', 'timeframe', 'status']


class EnquiryStatusForm(forms.ModelForm):
    """A simple form to update only the status of an enquiry."""
    class Meta:
        model = Enquiry
        fields = ['status']