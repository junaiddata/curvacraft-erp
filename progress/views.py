# progress/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DailyProgress
from .forms import SCOProgressUpdateForm, AdminReviewForm

@login_required
def daily_progress_detail(request, pk):
    report = get_object_or_404(DailyProgress, pk=pk)
    project = report.project
    user = request.user

    if not (user.role == 'admin' or user in project.assigned_scos.all()):
        messages.error(request, "You do not have permission to view this page.")
        return redirect('projects:dashboard')

    # --- NEW LOGIC: Determine user permissions in the view ---
    user_can_edit_sco_form = False
    if user.role == 'sco':
        # The logic is now much simpler: an SCO can edit if the report
        # is in the right status AND it is assigned to them.
        if report.status in ['PENDING', 'SUBMITTED'] and report.assigned_to == user:
            user_can_edit_sco_form = True

    user_can_edit_admin_form = False
    if user.role == 'admin' and report.status == 'SUBMITTED':
        user_can_edit_admin_form = True

    # --- Form Handling (remains the same) ---
    if request.method == 'POST':
        if 'submit_sco_progress' in request.POST and user_can_edit_sco_form:
            sco_form = SCOProgressUpdateForm(request.POST, request.FILES, instance=report)
            if sco_form.is_valid():
                progress = sco_form.save(commit=False)
                progress.status = 'SUBMITTED'
                progress.submitted_by = user
                progress.save()
                messages.success(request, 'Your progress has been saved.')
            else: messages.error(request, 'Error saving your progress.')
            return redirect('progress:daily_progress_detail', pk=report.pk)

        elif 'submit_admin_review' in request.POST and user_can_edit_admin_form:
            admin_form = AdminReviewForm(request.POST, instance=report)
            if admin_form.is_valid():
                review = admin_form.save(commit=False)
                review.status = 'REVIEWED'
                review.save()
                messages.success(request, 'The report has been reviewed and closed.')
            else: messages.error(request, 'Error saving your review.')
            return redirect('progress:daily_progress_detail', pk=report.pk)

    # --- Prepare for GET request ---
    sco_form = SCOProgressUpdateForm(instance=report)
    admin_form = AdminReviewForm(instance=report)

    context = {
        'report': report,
        'sco_form': sco_form,
        'admin_form': admin_form,
        'user_can_edit_sco_form': user_can_edit_sco_form,
        'user_can_edit_admin_form': user_can_edit_admin_form,
    }
    return render(request, 'progress/daily_progress_detail.html', context)




from .forms import SCOWeeklyUpdateForm, AdminWeeklyReviewForm
from .models import WeeklyProgress

@login_required
def weekly_progress_detail(request, pk):
    report = get_object_or_404(WeeklyProgress, pk=pk)
    project = report.project
    user = request.user

    if not (user.role == 'admin' or user in project.assigned_scos.all()):
        messages.error(request, "You do not have permission to view this page.")
        return redirect('projects:dashboard')

    # --- NEW LOGIC: Determine user permissions in the view ---
    user_can_edit_sco_form = False
    if user.role == 'sco':
        # The logic is now much simpler: an SCO can edit if the report
        # is in the right status AND it is assigned to them.
        if report.status in ['PENDING', 'SUBMITTED'] and report.assigned_to == user:
            user_can_edit_sco_form = True

    user_can_edit_admin_form = (user.role == 'admin' and report.status == 'SUBMITTED')


    # Form Handling
    if request.method == 'POST':
        if 'submit_sco_progress' in request.POST and user_can_edit_sco_form:
            form = SCOWeeklyUpdateForm(request.POST, request.FILES, instance=report)
            if form.is_valid():
                progress = form.save(commit=False)
                progress.status = 'SUBMITTED'
                progress.submitted_by = user
                progress.save()
                messages.success(request, 'Your weekly progress has been saved.')
            return redirect('progress:weekly_progress_detail', pk=report.pk)
        
        elif 'submit_admin_review' in request.POST and user_can_edit_admin_form:
            form = AdminWeeklyReviewForm(request.POST, instance=report)
            if form.is_valid():
                review = form.save(commit=False)
                review.status = 'REVIEWED'
                review.save()
                messages.success(request, 'The weekly report has been reviewed and closed.')
            return redirect('progress:weekly_progress_detail', pk=report.pk)

    sco_form = SCOWeeklyUpdateForm(instance=report)
    admin_form = AdminWeeklyReviewForm(instance=report)
    context = {
        'report': report,
        'sco_form': sco_form,
        'admin_form': admin_form,
        'user_can_edit_sco_form': user_can_edit_sco_form,
        'user_can_edit_admin_form': user_can_edit_admin_form,
    }
    return render(request, 'progress/weekly_progress_detail.html', context)