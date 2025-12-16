# enquiries/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Enquiry, Customer
from .forms import EnquiryForm, CustomerForm, EnquiryStatusForm , ExistingCustomerForm
from users.decorators import admin_required,role_required# Import the decorator



@role_required('admin','staff')
@login_required
def enquiry_list(request):
    enquiries = Enquiry.objects.all().order_by('-created_at')
    return render(request, 'enquiries/enquiry_list.html', {'enquiries': enquiries})

@login_required
@role_required('admin', 'staff')
def enquiry_create(request):
    # Initialize all forms to None or empty
    existing_customer_form = ExistingCustomerForm()
    new_customer_form = CustomerForm()
    enquiry_form = EnquiryForm()
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        enquiry_form = EnquiryForm(request.POST) # Always process the enquiry part

        customer_to_use = None
        is_customer_valid = False

        if form_type == 'existing':
            existing_customer_form = ExistingCustomerForm(request.POST)
            if existing_customer_form.is_valid():
                customer_to_use = existing_customer_form.cleaned_data['customer']
                is_customer_valid = True

        elif form_type == 'new':
            new_customer_form = CustomerForm(request.POST)
            if new_customer_form.is_valid():
                customer_to_use, created = Customer.objects.get_or_create(
                    email=new_customer_form.cleaned_data['email'],
                    defaults={
                        'name': new_customer_form.cleaned_data['name'],
                        'phone_number': new_customer_form.cleaned_data['phone_number'],
                        'address': new_customer_form.cleaned_data['address'],
                        'trn_number': new_customer_form.cleaned_data['trn_number'],
                    }
                )
                is_customer_valid = True
        
        # Now, check if both the customer part AND the enquiry part are valid
        if is_customer_valid and enquiry_form.is_valid():
            enquiry = enquiry_form.save(commit=False)
            enquiry.customer = customer_to_use
            enquiry.save()
            messages.success(request, 'Enquiry created successfully.')
            return redirect('enquiries:enquiry_list')
        else:
            # If anything failed, we will fall through and re-render the page
            # The forms will now contain the error messages
            messages.error(request, "Please correct the errors shown below.")

    # This context will be used for both GET requests and failed POST requests
    context = {
        'existing_customer_form': existing_customer_form,
        'new_customer_form': new_customer_form,
        'enquiry_form': enquiry_form
    }
    return render(request, 'enquiries/enquiry_form.html', context)


@role_required('admin','staff')

def enquiry_detail(request, pk):
    enquiry = get_object_or_404(Enquiry, pk=pk)
    
    # --- THIS IS THE CRITICAL LOGIC THAT WAS MISSING ---
    
    if request.method == 'POST':
        # If the page is submitted, process the status form
        status_form = EnquiryStatusForm(request.POST, instance=enquiry)
        if status_form.is_valid():
            status_form.save()
            messages.success(request, 'Enquiry status has been updated successfully.')
            # Redirect back to the same page to prevent re-posting on refresh
            return redirect('enquiries:enquiry_detail', pk=enquiry.pk)
    else:
        # For a normal page load (GET request), create a fresh form instance
        status_form = EnquiryStatusForm(instance=enquiry)

    context = {
        'enquiry': enquiry,
        'status_form': status_form  # Pass the form into the template
    }
    return render(request, 'enquiries/enquiry_detail.html', context)
@role_required('admin','staff')
@login_required
def enquiry_edit(request, pk):
    pass # To be implemented: Edit enquiry functionality



# --- THIS IS THE COMPLETED EDIT VIEW ---
@login_required
@role_required('admin', 'staff')
def enquiry_edit(request, pk):
    """Handles editing an existing enquiry and its associated customer."""
    enquiry = get_object_or_404(Enquiry, pk=pk)
    customer = enquiry.customer

    if request.method == 'POST':
        # Populate the forms with the POST data and the existing instances
        customer_form = CustomerForm(request.POST, instance=customer)
        enquiry_form = EnquiryForm(request.POST, instance=enquiry)
        
        if customer_form.is_valid() and enquiry_form.is_valid():
            customer_form.save()
            enquiry_form.save()
            messages.success(request, 'Enquiry has been updated successfully.')
            return redirect('enquiries:enquiry_detail', pk=enquiry.pk)
    else:
        # For a GET request, populate the forms with the existing data
        customer_form = CustomerForm(instance=customer)
        enquiry_form = EnquiryForm(instance=enquiry)
    
    context = {
        'customer_form': customer_form,
        'enquiry_form': enquiry_form,
        'enquiry': enquiry,
        'action': 'Edit' # To change the title on the form page
    }
    # We can reuse the same form template for both create and edit
    return render(request, 'enquiries/enquiry_form.html', context)

# --- THIS IS THE NEW DELETE VIEW ---
@login_required
@role_required('admin') # Only admins should be able to delete
def enquiry_delete(request, pk):
    """Handles the confirmation and deletion of an enquiry."""
    enquiry = get_object_or_404(Enquiry, pk=pk)
    
    if request.method == 'POST':
        # If the confirmation form is submitted, delete the object
        customer_name = enquiry.customer.name # Get name before deleting
        enquiry.delete()
        messages.warning(request, f"Enquiry for {customer_name} has been permanently deleted.")
        return redirect('enquiries:enquiry_list')
    
    # For a GET request, show the confirmation page
    context = {'enquiry': enquiry}
    return render(request, 'enquiries/enquiry_confirm_delete.html', context)



# ==================================
# CUSTOMER MANAGEMENT VIEWS
# ==================================

@login_required
@role_required('admin', 'staff')
def customer_list(request):
    """Displays a searchable list of all customers."""
    customers = Customer.objects.all().order_by('name')
    context = {'customers': customers}
    return render(request, 'enquiries/customer_list.html', context)

@login_required
@role_required('admin', 'staff')
def customer_detail(request, pk):
    """Displays details for a single customer and lists their associated projects."""
    customer = get_object_or_404(Customer, pk=pk)
    # We prefetch related projects for efficiency
    customer_projects = customer.projects.prefetch_related('quotation__enquiry').all()
    context = {
        'customer': customer,
        'projects': customer_projects
    }
    return render(request, 'enquiries/customer_detail.html', context)

@login_required
@role_required('admin', 'staff')
def customer_edit(request, pk):
    """Handles editing an existing customer's details."""
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f"Details for {customer.name} have been updated.")
            return redirect('enquiries:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
        
    context = {
        'form': form,
        'customer': customer
    }
    return render(request, 'enquiries/customer_edit_form.html', context)

@login_required
@role_required('admin') # Only admins can delete customers
def customer_delete(request, pk):
    """Handles the confirmation and deletion of a customer."""
    customer = get_object_or_404(Customer, pk=pk)
    if customer.projects.exists() or customer.enquiries.exists():
        messages.error(request, f"Cannot delete {customer.name} because they are linked to existing projects or enquiries.")
        return redirect('enquiries:customer_detail', pk=customer.pk)
        
    if request.method == 'POST':
        customer.delete()
        messages.warning(request, f"Customer {customer.name} has been permanently deleted.")
        return redirect('enquiries:customer_list')
        
    context = {'customer': customer}
    return render(request, 'enquiries/customer_confirm_delete.html', context)