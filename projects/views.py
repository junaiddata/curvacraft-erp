# projects/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Project, ProjectItem , MilestonePhase# Add ProjectItem
from django.shortcuts import render, get_object_or_404 # Add get_object_or_404
from progress.forms import DailyTaskCreationForm # Import our new form
from progress.models import DailyProgress
from django.contrib import messages # Import the messages framework
from django.db.models import Q
from progress.forms import WeeklyTaskCreationForm # Add this import
from progress.models import WeeklyProgress # Add this import
import datetime # Add this import
from quotations.models import Quotation # Import the Quotation model
from .forms import ProjectForm, MilestoneTaskFormSet# Import our new form
from users.decorators import admin_required,role_required # Import the decorator
from enquiries.forms import CustomerForm # Import the CustomerForm
from enquiries.models import Customer


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
                # --- THIS IS THE NEW, CORRECT LOGIC ---
        # 3. Create the fixed Milestone Phase headers for the new project
        MilestonePhase.objects.create(project=new_project, name="Kick off meeting", details="Phase 1- Module 1 & 2", default_timeline="1-3 days", order=10)
        MilestonePhase.objects.create(project=new_project, name="Concept Design", details="Phase 2- Module 3,4 & 5", default_timeline="4 weeks", order=20)
        MilestonePhase.objects.create(project=new_project, name="Detail Design", details="Phase 3- Module 6,7& 8", default_timeline="3 weeks", order=30)
        MilestonePhase.objects.create(project=new_project, name="Estimation", details="Phase 4", order=40)
        # --- END OF NEW LOGIC ---

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



# projects/views.py
from django.forms import formset_factory, modelformset_factory

# --- THIS IS THE NEW VIEW for the read-only page ---
@login_required
@role_required('admin')
def project_tracking_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    # We prefetch the related tasks for a huge performance boost
    phases = project.milestone_phases.prefetch_related('tasks')
    context = {
        'project': project,
        'phases': phases,
    }
    return render(request, 'projects/project_tracking_detail.html', context)


# --- THIS IS YOUR RENAMED VIEW for the form/edit page ---
# projects/views.py
from .forms import MilestonePhaseFormSet, MilestoneTaskFormSet
from .models import Project, MilestonePhase # Make sure MilestonePhase is imported

@login_required
@role_required('admin')
def project_tracking_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # We get the queryset of phases for this project to pass to the main formset
    phase_queryset = MilestonePhase.objects.filter(project=project)

    if request.method == 'POST':
        # Create the main formset for the phases from the POST data
        phase_formset = MilestonePhaseFormSet(request.POST, queryset=phase_queryset, prefix='phases')
        
        # We also need to create instances of the nested task formsets with the POST data
        nested_task_formsets = []
        for phase in phase_queryset:
            task_formset = MilestoneTaskFormSet(request.POST, instance=phase, prefix=f'tasks-{phase.pk}')
            nested_task_formsets.append(task_formset)

        # Validate everything at once
        if phase_formset.is_valid() and all(fs.is_valid() for fs in nested_task_formsets):
            phase_formset.save() # Save the changes to the Phase timelines
            for fs in nested_task_formsets:
                fs.save() # Save the changes to the Tasks
            
            messages.success(request, 'Tracking schedule has been updated.')
            return redirect('projects:project_tracking_detail', pk=project.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # For a GET request, create the unbound formsets
        phase_formset = MilestonePhaseFormSet(queryset=phase_queryset, prefix='phases')
        nested_task_formsets = []
        for phase in phase_queryset:
            task_formset = MilestoneTaskFormSet(instance=phase, prefix=f'tasks-{phase.pk}')
            nested_task_formsets.append(task_formset)

    # Zip the individual forms from the phase_formset with their corresponding task formset
    # This gives the template everything it needs in one loop
    phase_and_formsets_zipped = zip(phase_formset, nested_task_formsets)
    
    context = {
        'project': project,
        'phase_formset': phase_formset, # This is needed for the management form
        'phase_and_formsets_zipped': phase_and_formsets_zipped, # This is for the main loop
    }
    return render(request, 'projects/project_tracking_form.html', context)





# --- ADD THIS NEW VIEW ---
@login_required
@role_required('admin')
def project_create_direct(request):
    if request.method == 'POST':
        # We are submitting all three forms at once
        customer_form = CustomerForm(request.POST)
        project_form = ProjectForm(request.POST) # A simplified project form
        formset = ProjectItemFormSet(request.POST)

        if customer_form.is_valid() and project_form.is_valid() and formset.is_valid():
            # 1. Get or create the customer
            customer, created = Customer.objects.get_or_create(
                email=customer_form.cleaned_data['email'],
                defaults={'name': customer_form.cleaned_data['name']}
            )
            
            # 2. Save the project, linking the customer
            project = project_form.save(commit=False)
            project.customer = customer
            project.save() # Save the project to get a PK

            # 3. Save the project items, linking them to the new project
            formset.instance = project
            formset.save()
            
            # Also save the ManyToMany field for SCOs
            project_form.save_m2m()

            messages.success(request, 'Direct project created successfully!')
            return redirect('projects:project_detail', pk=project.pk)
    else:
        customer_form = CustomerForm()
        project_form = ProjectForm()
        formset = ProjectItemFormSet(queryset=ProjectItem.objects.none())

    context = {
        'customer_form': customer_form,
        'project_form': project_form,
        'formset': formset
    }
    return render(request, 'projects/project_create_direct_form.html', context)