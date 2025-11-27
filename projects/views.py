# projects/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Project, ProjectItem # Add ProjectItem
from django.shortcuts import render, get_object_or_404 # Add get_object_or_404
from progress.forms import DailyTaskCreationForm # Import our new form
from progress.models import DailyProgress
from django.contrib import messages # Import the messages framework
from django.db.models import Q
from progress.forms import WeeklyTaskCreationForm # Add this import
from progress.models import WeeklyProgress # Add this import
import datetime # Add this import
from quotations.models import Quotation # Import the Quotation model
from .forms import ProjectForm # Import our new form
from users.decorators import admin_required,role_required # Import the decorator


@login_required
def dashboard(request):
    # Check the role of the logged-in user
    if request.user.role == 'admin':
        # Admin sees all projects
        projects = Project.objects.all().order_by('-created_at')
        template_name = 'projects/project_list.html'
    else: # The user is an SCO
        # SCO sees only their assigned projects
        projects = Project.objects.filter(assigned_scos=request.user).order_by('-created_at')
        template_name = 'projects/sco_dashboard.html'
    
    context = {
        'projects': projects
    }
    return render(request, template_name, context)


@login_required
@role_required('admin')
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.method == 'POST' and 'add_daily_task' in request.POST:
        task_form = DailyTaskCreationForm(request.POST, project=project)
        if task_form.is_valid():
            date = task_form.cleaned_data['date']
            assigned_sco = task_form.cleaned_data.get('assigned_to')
            planned_task = task_form.cleaned_data['planned_task']
            
            # --- NEW LOGIC: Generate Tasks ---
            if assigned_sco:
                # Logic for a single, specific SCO
                if DailyProgress.objects.filter(project=project, date=date, assigned_to=assigned_sco).exists():
                    messages.error(request, f'A task for {date} is already assigned to {assigned_sco.username}.')
                else:
                    DailyProgress.objects.create(
                        project=project, date=date, assigned_to=assigned_sco, planned_task=planned_task
                    )
                    messages.success(request, f'New daily task for {assigned_sco.username} has been added.')
            else:
                # Logic for "All SCOs": Loop and create for each
                scos_on_project = project.assigned_scos.all()
                if not scos_on_project:
                     messages.warning(request, 'No SCOs are assigned to this project to create tasks for.')
                else:
                    created_count = 0
                    for sco in scos_on_project:
                        if not DailyProgress.objects.filter(project=project, date=date, assigned_to=sco).exists():
                            DailyProgress.objects.create(
                                project=project, date=date, assigned_to=sco, planned_task=planned_task
                            )
                            created_count += 1
                    messages.success(request, f'{created_count} new tasks were created for all assigned SCOs.')
            return redirect('projects:project_detail', pk=project.pk)

    # --- NEW, SIMPLIFIED FILTERING LOGIC FOR SCOs ---
    task_form = DailyTaskCreationForm(project=project)
    if request.user.role == 'admin':
        progress_reports = DailyProgress.objects.filter(project=project).order_by('-date')
    else: # SCO only sees tasks assigned to them
        progress_reports = DailyProgress.objects.filter(project=project, assigned_to=request.user).order_by('-date')

    context = { 'project': project, 'progress_reports': progress_reports, 'task_form': task_form }
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_weekly_reports(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.method == 'POST' and request.user.role == 'admin':
        form = WeeklyTaskCreationForm(request.POST, project=project)
        if form.is_valid():
            date = form.cleaned_data['week_start_date']
            monday = date - datetime.timedelta(days=date.weekday())
            assigned_sco = form.cleaned_data.get('assigned_to')
            planned_task = form.cleaned_data['planned_task']
            
            # --- NEW LOGIC: Generate Weekly Tasks ---
            if assigned_sco:
                # Logic for a single, specific SCO
                if WeeklyProgress.objects.filter(project=project, week_start_date=monday, assigned_to=assigned_sco).exists():
                    messages.error(request, f'A weekly report for {assigned_sco.username} starting {monday} already exists.')
                else:
                    WeeklyProgress.objects.create(
                        project=project,
                        week_start_date=monday,
                        assigned_to=assigned_sco,
                        planned_task=planned_task
                    )
                    messages.success(request, f'New weekly report for {assigned_sco.username} has been added.')
            else:
                # Logic for "All SCOs": Loop and create for each
                scos_on_project = project.assigned_scos.all()
                if not scos_on_project:
                     messages.warning(request, 'No SCOs are assigned to this project to create reports for.')
                else:
                    created_count = 0
                    for sco in scos_on_project:
                        # Check for duplicates for each SCO before creating
                        if not WeeklyProgress.objects.filter(project=project, week_start_date=monday, assigned_to=sco).exists():
                            WeeklyProgress.objects.create(
                                project=project,
                                week_start_date=monday,
                                assigned_to=sco,
                                planned_task=planned_task
                            )
                            created_count += 1
                    messages.success(request, f'{created_count} new weekly reports were created for all assigned SCOs.')
            return redirect('projects:project_weekly_reports', pk=project.pk)
        else:
            messages.error(request, 'Please correct the errors below.')


    # --- SIMPLIFIED FILTERING LOGIC FOR SCOs ---
    form = WeeklyTaskCreationForm(project=project)
    if request.user.role == 'admin':
        # Admin sees all weekly reports for the project
        weekly_reports = WeeklyProgress.objects.filter(project=project).order_by('-week_start_date')
    else:
        # SCO only sees weekly reports assigned to them
        weekly_reports = WeeklyProgress.objects.filter(project=project, assigned_to=request.user).order_by('-week_start_date')

    context = {
        'project': project,
        'form': form,
        'weekly_reports': weekly_reports
    }
    return render(request, 'projects/project_weekly_reports.html', context)


@role_required('admin')
@login_required
def create_project_from_quotation(request, quotation_pk):
    """
    Handles the creation of a Project from an accepted Quotation.
    """
    quotation = get_object_or_404(Quotation, pk=quotation_pk)

    # Prevent creating a project if one already exists for this quote
    if hasattr(quotation, 'project'):
        messages.warning(request, 'A project already exists for this quotation.')
        return redirect('projects:project_detail', pk=quotation.project.pk)

    if request.method == 'POST':
        # 1. Create the new project
        new_project = Project.objects.create(
            quotation=quotation,
            title=f"Project for {quotation.enquiry.customer.name}",
            # Copy the tax rate from the quote as a starting point
            tax_percentage=quotation.tax_percentage 
        )

        # 2. Loop through quote items and create project items
        for item in quotation.items.all():
            ProjectItem.objects.create(
                project=new_project,
                description=item.description,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price
            )

        # 3. Update the quotation's status
        quotation.status = 'ACCEPTED'
        quotation.save()

        messages.success(request, 'Project created successfully! Please review the final budget and assign SCOs.')
        # Redirect to the new project's edit page
        return redirect('projects:project_edit', pk=new_project.pk)

    # If it's a GET request, show the confirmation page
    context = {'quotation': quotation}
    return render(request, 'projects/project_confirm_creation.html', context)

from .forms import ProjectForm, ProjectItemFormSet # Add ProjectItemFormSet

@role_required('admin')
@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        formset = ProjectItemFormSet(request.POST, instance=project)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Project details have been updated.')
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
        formset = ProjectItemFormSet(instance=project)

    context = {'form': form, 'formset': formset, 'project': project} # Add formset
    return render(request, 'projects/project_form.html', context)



@login_required
def project_daily_tasks(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # Handle the "Add Task" form submission
    if request.method == 'POST' and request.user.role == 'admin':
        task_form = DailyTaskCreationForm(request.POST, project=project)
        if task_form.is_valid():
            date = task_form.cleaned_data['date']
            assigned_sco = task_form.cleaned_data.get('assigned_to')
            planned_task = task_form.cleaned_data['planned_task']
            
            # --- NEW LOGIC: Generate Tasks ---
            if assigned_sco:
                # Logic for a single, specific SCO
                if DailyProgress.objects.filter(project=project, date=date, assigned_to=assigned_sco).exists():
                    messages.error(request, f'A task for {date} is already assigned to {assigned_sco.username}.')
                else:
                    DailyProgress.objects.create(
                        project=project, date=date, assigned_to=assigned_sco, planned_task=planned_task
                    )
                    messages.success(request, f'New daily task for {assigned_sco.username} has been added.')
            else:
                # Logic for "All SCOs": Loop and create for each
                scos_on_project = project.assigned_scos.all()
                if not scos_on_project:
                     messages.warning(request, 'No SCOs are assigned to this project to create tasks for.')
                else:
                    created_count = 0
                    for sco in scos_on_project:
                        if not DailyProgress.objects.filter(project=project, date=date, assigned_to=sco).exists():
                            DailyProgress.objects.create(
                                project=project, date=date, assigned_to=sco, planned_task=planned_task
                            )
                            created_count += 1
                    messages.success(request, f'{created_count} new tasks were created for all assigned SCOs.')
            return redirect('projects:project_detail', pk=project.pk)

    
    # Prepare data for GET request
    task_form = DailyTaskCreationForm(project=project)
    if request.user.role == 'admin':
        progress_reports = DailyProgress.objects.filter(project=project).order_by('-date')
    else:
        progress_reports = DailyProgress.objects.filter(project=project, assigned_to=request.user).order_by('-date')

    context = {
        'project': project,
        'task_form': task_form,
        'progress_reports': progress_reports
    }
    return render(request, 'projects/project_daily_tasks.html', context)


# --- ADD THIS NEW VIEW ---
@login_required
def get_scos_as_html(request):
    """
    An API-like view that returns a rendered HTML snippet of the
    'assigned_scos' field from a fresh ProjectForm.
    """
    # Create a fresh, unbound form to get the latest choices
    form = ProjectForm() 
    return render(request, 'projects/partials/sco_checkbox_list.html', {'form': form})