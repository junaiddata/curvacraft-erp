# accounts/views.py
from django.shortcuts import render
from projects.models import Project # To get global stats
from invoices.models import Invoice
from .forms import PaymentForm, CreditNoteForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from users.decorators import admin_required
from decimal import Decimal
from django.http import HttpResponse
import csv
from django.utils import timezone

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from projects.models import Project
from users.decorators import admin_required

@login_required
@admin_required
def accounts_dashboard(request):
    """
    Displays a high-level financial overview of all projects, including calculated percentages.
    """
    all_projects = Project.objects.prefetch_related(
        'project_items', 'invoices__payments', 'invoices__credit_notes'
    ).all()

    # --- Calculate Grand Totals ---
    total_project_value = sum(p.subtotal for p in all_projects)
    total_amount_invoiced_grand = sum(p.total_invoiced_grand for p in all_projects)
    total_amount_received = sum(p.total_received for p in all_projects)
    total_accounts_receivable = sum(p.accounts_receivable for p in all_projects)

    # --- Calculate Percentages Safely in Python ---
    invoicing_percentage = 0
    if total_project_value > 0:
        total_invoiced_subtotal = sum(p.total_invoiced_subtotal for p in all_projects)
        invoicing_percentage = (total_invoiced_subtotal / total_project_value) * 100

    payment_percentage = 0
    if total_amount_invoiced_grand > 0:
        payment_percentage = (total_amount_received / total_amount_invoiced_grand) * 100

    context = {
        'projects': all_projects,
        'total_project_value': total_project_value,
        'total_amount_invoiced': total_amount_invoiced_grand,
        'total_amount_received': total_amount_received,
        'total_pending': total_accounts_receivable,
        'invoicing_percentage': invoicing_percentage, # Pass the final number
        'payment_percentage': payment_percentage,   # Pass the final number
    }
    return render(request, 'accounts/dashboard.html', context)
    
@login_required
@admin_required
def add_payment(request, invoice_pk):
    invoice = get_object_or_404(Invoice, pk=invoice_pk)

    # Pre-fill the form with the remaining amount due
    initial_data = {'amount': invoice.amount_due}

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            
            # Prevent over-payment
            if payment.amount > invoice.amount_due:
                messages.error(request, f"Payment amount cannot be greater than the amount due ({invoice.amount_due:,.2f}).")
            else:
                payment.save()
                messages.success(request, f"Payment of {payment.amount:,.2f} recorded successfully for invoice {invoice.invoice_number}.")
                
                # Optional: Automatically update invoice status if fully paid
                if invoice.amount_due <= 0:
                    invoice.status = 'PAID'
                    invoice.save()
                    messages.info(request, f"Invoice {invoice.invoice_number} is now fully paid.")
                    
                return redirect('invoices:invoice_detail', pk=invoice.pk)
    else:
        form = PaymentForm(initial=initial_data)

    context = {
        'form': form,
        'invoice': invoice
    }
    return render(request, 'accounts/payment_form.html', context)

@login_required
@admin_required
def add_credit_note(request, invoice_pk):
    invoice = get_object_or_404(Invoice, pk=invoice_pk)

    if request.method == 'POST':
        form = CreditNoteForm(request.POST)
        if form.is_valid():
            credit_note = form.save(commit=False)
            
            # --- THIS IS THE CORRECTED VALIDATION ---
            
            # Calculate what the total credited amount WOULD BE if we add this new one.
            potential_total_credited = invoice.total_credited + credit_note.amount
            
            # A credit note is valid as long as the total credited amount does not exceed
            # the invoice's original grand total.
            if potential_total_credited > invoice.grand_total:
                # Calculate the maximum allowable credit
                max_credit = invoice.grand_total - invoice.total_credited
                messages.error(request, f"Total credit cannot exceed the invoice total. Maximum additional credit allowed is {max_credit:,.2f}.")
            else:
                credit_note.invoice = invoice
                credit_note.save()
                messages.success(request, f"Credit note {credit_note.credit_note_number} issued successfully against invoice {invoice.invoice_number}.")
                
                # Automatically update invoice status if fully paid/credited
                if invoice.amount_due <= 0:
                    invoice.status = 'PAID'
                    invoice.save()
                    messages.info(request, f"Invoice {invoice.invoice_number} is now fully paid/credited.")
                    
                return redirect('invoices:invoice_detail', pk=invoice.pk)
    else:
        form = CreditNoteForm()

    context = {
        'form': form,
        'invoice': invoice
    }
    return render(request, 'accounts/credit_note_form.html', context)


# --- ADD THIS NEW VIEW ---
@login_required
@admin_required
def export_project_summary_csv(request):
    """
    Generates and streams a CSV file of the project financial summary.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="curvacraft_project_summary_{timezone.now():%Y-%m-%d}.csv"'

    writer = csv.writer(response)
    # Write the header row
    writer.writerow([
        'Project Title', 'Customer', 'Status',
        'Project Budget (excl. VAT)', 'Total Billed (incl. VAT)',
        'Budget Remaining to Invoice', 'Total Received (Payments)',
        'Accounts Receivable'
    ])

    # Fetch all projects with prefetched data for efficiency
    projects = Project.objects.prefetch_related('invoices__payments', 'invoices__credit_notes', 'project_items').all()

    # Write data rows
    for project in projects:
        writer.writerow([
            project.title,
            project.customer.name,
            project.get_status_display(),
            f"{project.subtotal:.2f}",
            f"{project.total_invoiced_grand:.2f}",
            f"{project.budget_remaining_to_invoice_grand:.2f}",
            f"{project.total_received:.2f}",
            f"{project.accounts_receivable:.2f}"
        ])
        
    return response