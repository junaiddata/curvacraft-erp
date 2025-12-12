# core/views.py
from django.shortcuts import render, redirect
from projects.models import Project
from enquiries.models import Enquiry
from quotations.models import Quotation
from progress.models import DailyProgress
from django.db.models import Prefetch # Add this import
from reports.models import DailyReport # Add this import



def home_view(request):
    # If the user is not logged in, show a simple landing page.
    if not request.user.is_authenticated:
        return render(request, 'core/landing_page.html')

    # --- THIS IS THE CORRECTED LOGIC ---

    # 1. Handle ADMIN role
    if request.user.role == 'admin':
        # Gather stats and show the ERP dashboard for admins.
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
    
    # 2. Handle STAFF role
    elif request.user.role == 'staff':
        # For staff, redirect them directly to the page they care about most.
        return redirect('enquiries:enquiry_list')
    
    # 3. Handle SCO role (this is now the final 'else')
    else: # SCO
        # --- THIS IS THE MODIFIED QUERY ---
        # We want to get the 3 most recent reports for each project
        recent_reports = DailyReport.objects.order_by('-date')

        assigned_projects = Project.objects.filter(
            assigned_scos=request.user
        ).prefetch_related(
            # Prefetch only the 3 most recent reports for each project
            Prefetch('daily_reports', queryset=recent_reports, to_attr='recent_dprs')
        ).order_by('status')
        
        context = {
            'projects': assigned_projects
        }
        return render(request, 'projects/sco_dashboard.html', context)