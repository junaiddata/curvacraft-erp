# core/views.py
from django.shortcuts import render
from projects.models import Project
from enquiries.models import Enquiry
from quotations.models import Quotation
from progress.models import DailyProgress

def home_view(request):
    # If the user is not logged in, show a simple landing page.
    if not request.user.is_authenticated:
        return render(request, 'core/landing_page.html')

    # If the user is an ADMIN, gather stats and show the ERP dashboard.
    if request.user.role == 'admin':
        # --- Gather Statistics for the Dashboard ---
        active_projects_count = Project.objects.filter(status='IN_PROGRESS').count()
        pending_enquiries_count = Enquiry.objects.filter(status='PENDING').count()
        quotes_awaiting_acceptance = Quotation.objects.filter(status='SENT').count()
        reports_to_review_count = DailyProgress.objects.filter(status='SUBMITTED').count()

        context = {
            'active_projects_count': active_projects_count,
            'pending_enquiries_count': pending_enquiries_count,
            'quotes_awaiting_acceptance': quotes_awaiting_acceptance,
            'reports_to_review_count': reports_to_review_count,
        }
        return render(request, 'core/admin_dashboard.html', context)
    
    # If the user is an SCO, show their assigned projects.
    else:
        assigned_projects = Project.objects.filter(assigned_scos=request.user).order_by('status')
        context = {
            'projects': assigned_projects
        }
        # We can reuse the project dashboard template for this
        return render(request, 'projects/sco_dashboard.html', context)