# enquiries/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Enquiry, Customer
from .forms import EnquiryForm, CustomerForm, EnquiryStatusForm
from users.decorators import admin_required # Import the decorator



@admin_required
@login_required
def enquiry_list(request):
    enquiries = Enquiry.objects.all().order_by('-created_at')
    return render(request, 'enquiries/enquiry_list.html', {'enquiries': enquiries})

@admin_required
@login_required
def enquiry_create(request):
    if request.method == 'POST':
        customer_form = CustomerForm(request.POST)
        enquiry_form = EnquiryForm(request.POST)
        if customer_form.is_valid() and enquiry_form.is_valid():
            # Check if customer already exists
            customer, created = Customer.objects.get_or_create(
                email=customer_form.cleaned_data['email'],
                defaults={'name': customer_form.cleaned_data['name'], 
                          'phone_number': customer_form.cleaned_data['phone_number'],
                          'address': customer_form.cleaned_data['address']}
            )
            enquiry = enquiry_form.save(commit=False)
            enquiry.customer = customer
            enquiry.save()
            messages.success(request, 'Enquiry created successfully.')
            return redirect('enquiries:enquiry_list')
    else:
        customer_form = CustomerForm()
        enquiry_form = EnquiryForm()
    
    context = {'customer_form': customer_form, 'enquiry_form': enquiry_form}
    return render(request, 'enquiries/enquiry_form.html', context)


@login_required
@admin_required
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
@admin_required
@login_required
def enquiry_edit(request, pk):
    pass # To be implemented: Edit enquiry functionality

