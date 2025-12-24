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
from enquiries.forms import CustomerForm ,ExistingCustomerForm # Import the CustomerForm
from enquiries.models import Customer

import io
from django.http import FileResponse
from invoices.pdf_utils import NumberedCanvas, process_logo, LineSeparator # Reuse our helpers
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape # Use landscape for wide tables
from reportlab.lib.units import inch


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


@login_required
@role_required('admin')
def create_project_from_quotation(request, quotation_pk):
    """
    Handles the complete creation of a Project from an accepted Quotation.
    """
    quotation = get_object_or_404(Quotation, pk=quotation_pk)

    # Prevent creating a project if one already exists for this quote
    if hasattr(quotation, 'project') and quotation.project is not None:
        messages.warning(request, 'A project already exists for this quotation.')
        return redirect('projects:project_detail', pk=quotation.project.pk)

    if request.method == 'POST':
        # --- This is the complete and correct sequence ---

        # 1. Create the new project object with ALL required fields
        new_project = Project.objects.create(
            quotation=quotation,
            title=f"Project for {quotation.enquiry.customer.name}",
            customer=quotation.enquiry.customer,  # <-- The fix for the IntegrityError
            location=quotation.enquiry.location,  # <-- The fix for the IntegrityError
            tax_percentage=quotation.tax_percentage 
        )

        # 2. Loop through quote items and create project items for the new project
        for item in quotation.items.all():
            ProjectItem.objects.create(
                project=new_project,
                description=item.description,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price
            )

        # 3. Create the fixed Milestone Phase headers for the new project
        MilestonePhase.objects.create(project=new_project, name="Kick off meeting", details="Phase 1- Module 1 & 2", default_timeline="1-3 days", order=10)
        MilestonePhase.objects.create(project=new_project, name="Concept Design", details="Phase 2- Module 3,4 & 5", default_timeline="4 weeks", order=20)
        MilestonePhase.objects.create(project=new_project, name="Detail Design", details="Phase 3- Module 6,7& 8", default_timeline="3 weeks", order=30)
        MilestonePhase.objects.create(project=new_project, name="Estimation", details="Phase 4", order=40)

        # 4. Update the quotation's status to 'Accepted'
        quotation.status = 'ACCEPTED'
        quotation.save()

        messages.success(request, 'Project created successfully! Please review the final details and assign SCOs.')
        # Redirect to the new project's EDIT page to finalize
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
    
    fitout_quote_exists = False
    if project.quotation:
        fitout_quote_exists = Quotation.objects.filter(
            enquiry=project.quotation.enquiry, 
            quote_type='FITOUT'
        ).exists()

    context = {'form': form, 'formset': formset, 'project': project,'fitout_quote_exists': fitout_quote_exists} # Add formset
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

import io
import datetime
import requests
from io import BytesIO
from PIL import Image as PILImage, ImageOps
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.pdfgen import canvas


# ============================================================
# COLOR PALETTE (Light Purple/Lavender Theme - As Per Design)
# ============================================================
COLORS = {
    'header_bg': colors.HexColor("#D8D8F0"),          # Light lavender (header row)
    'phase_bg': colors.HexColor("#E8E8F8"),           # Lighter lavender (phase rows)
    'row_white': colors.HexColor("#FFFFFF"),          # White (task rows)
    'border': colors.HexColor("#000000"),             # Black borders
    'text_dark': colors.HexColor("#000000"),          # Black text
    'text_brown': colors.HexColor("#5D4E37"),         # Brown text for headers
}


class NumberedCanvas(canvas.Canvas):
    """Custom Canvas for page numbering."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        page_width, page_height = landscape(letter)
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#666666"))
        self.drawRightString(
            page_width - 0.5 * inch,
            0.4 * inch,
            f"Page {self._pageNumber} of {page_count}"
        )


def process_logo_inverted(logo_url, max_width=1.5*inch, max_height=0.6*inch):
    """
    Fetches logo from URL, inverts colors, returns ReportLab Image or None.
    """
    try:
        response = requests.get(logo_url, timeout=10)
        response.raise_for_status()
        img_data = BytesIO(response.content)
        
        pil_img = PILImage.open(img_data)
        
        if pil_img.mode != 'RGBA':
            pil_img = pil_img.convert('RGBA')
        
        r, g, b, a = pil_img.split()
        rgb_image = PILImage.merge('RGB', (r, g, b))
        inverted_rgb = ImageOps.invert(rgb_image)
        r_inv, g_inv, b_inv = inverted_rgb.split()
        pil_img = PILImage.merge('RGBA', (r_inv, g_inv, b_inv, a))
        
        img_width, img_height = pil_img.size
        aspect = img_width / img_height
        
        if img_width / max_width > img_height / max_height:
            width = max_width
            height = max_width / aspect
        else:
            height = max_height
            width = max_height * aspect
        
        output = BytesIO()
        pil_img.save(output, format='PNG')
        output.seek(0)
        
        return Image(output, width=width, height=height)
    
    except Exception as e:
        print(f"Logo processing error: {e}")
        return None


@login_required
@role_required('admin')
def project_tracking_pdf(request, pk):
    """Generates a professional Project Milestone Tracking PDF matching the design."""
    project = get_object_or_404(Project, pk=pk)
    phases = project.milestone_phases.prefetch_related('tasks')

    buf = io.BytesIO()
    
    # Landscape with good margins
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(letter),
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.6 * inch
    )
    
    page_width = landscape(letter)[0] - 1.2 * inch  # Available width

    # --- STYLES ---
    styles = getSampleStyleSheet()

    custom_styles = {
        'PTMainTitle': ParagraphStyle(
            name='PTMainTitle',
            fontName='Helvetica-Bold',
            fontSize=18,
            alignment=TA_CENTER,
            textColor=COLORS['text_dark'],
            spaceAfter=0
        ),
        'PTLogoText': ParagraphStyle(
            name='PTLogoText',
            fontName='Helvetica',
            fontSize=14,
            alignment=TA_LEFT,
            textColor=COLORS['text_dark'],
            leading=18
        ),
        'PTProjectLabel': ParagraphStyle(
            name='PTProjectLabel',
            fontName='Helvetica',
            fontSize=11,
            alignment=TA_LEFT,
            textColor=COLORS['text_dark'],
            leading=14
        ),
        'PTTableHeader': ParagraphStyle(
            name='PTTableHeader',
            fontName='Helvetica-Bold',
            fontSize=10,
            alignment=TA_LEFT,
            textColor=COLORS['text_dark'],
            leading=12
        ),
        'PTTableHeaderCenter': ParagraphStyle(
            name='PTTableHeaderCenter',
            fontName='Helvetica-Bold',
            fontSize=10,
            alignment=TA_CENTER,
            textColor=COLORS['text_dark'],
            leading=12
        ),
        'PTPhaseCell': ParagraphStyle(
            name='PTPhaseCell',
            fontName='Helvetica-Bold',
            fontSize=10,
            alignment=TA_LEFT,
            textColor=COLORS['text_dark'],
            leading=12
        ),
        'PTTableCell': ParagraphStyle(
            name='PTTableCell',
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_LEFT,
            textColor=COLORS['text_dark'],
            leading=12
        ),
        'PTTableCellCenter': ParagraphStyle(
            name='PTTableCellCenter',
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_CENTER,
            textColor=COLORS['text_dark'],
            leading=12
        ),
    }

    for style_name, style in custom_styles.items():
        if style_name not in styles.byName:
            styles.add(style)

    # --- BUILD STORY ---
    story = []

    # ============================================================
    # HEADER SECTION (Logo on left, Title on right)
    # ============================================================
    
    logo_url = "https://curvacraft.com/wp-content/uploads/2024/10/Curvacraft-logo-1024x255.webp"
    logo = process_logo_inverted(logo_url, max_width=1.8*inch, max_height=0.7*inch)
    
    # Logo with company name
    if logo:
        logo_cell = logo
    else:
        logo_cell = Paragraph("<b>CURVACRAFT</b>", styles['PTLogoText'])
    
    # Title
    title_cell = Paragraph("<b>Project Milestone Tracking</b>", styles['PTMainTitle'])
    
    # Header table
    header_data = [[logo_cell, title_cell]]
    header_table = Table(header_data, colWidths=[3.0*inch, page_width - 3.0*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.25 * inch))

    # ============================================================
    # PROJECT NAME
    # ============================================================
    
    project_label = Paragraph(f"<b>Project:</b> {project.title}", styles['PTProjectLabel'])
    story.append(project_label)
    story.append(Spacer(1, 0.3 * inch))

    # ============================================================
    # MILESTONE TABLE
    # ============================================================
    
    # Column widths (matching your design proportions)
    col_widths = [
        0.8 * inch,     # Sl.No
        4.0 * inch,     # Design Phases
        1.5 * inch,     # Timelines as per contract
        1.5 * inch,     # Invoices Submitted
        1.7 * inch,     # Amount received Date
    ]
    
    # Scale to fit page width
    total_col_width = sum(col_widths)
    scale_factor = page_width / total_col_width
    col_widths = [w * scale_factor for w in col_widths]

    # Table header row
    table_data = [
        [
            Paragraph('<b>Sl.No</b>', styles['PTTableHeader']),
            Paragraph('<b>Design Phases</b>', styles['PTTableHeader']),
            Paragraph('<b>Timelines as per<br/>contract</b>', styles['PTTableHeader']),
            Paragraph('<b>Invoices Submitted</b>', styles['PTTableHeader']),
            Paragraph('<b>Amount received Date</b>', styles['PTTableHeader']),
        ]
    ]
    
    # Base table styles
    table_style = [
        # Header styling (light lavender)
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['header_bg']),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Good padding for readability
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        
        # Black grid borders
        ('GRID', (0, 0), (-1, -1), 1, COLORS['border']),
    ]
    
    current_row_index = 1

    for phase in phases:
        # --------------------------------------------------------
        # PHASE HEADER ROW (Light lavender background)
        # --------------------------------------------------------
        phase_details = phase.details if phase.details else ''
        phase_name = phase.name if phase.name else ''
        phase_timeline = phase.default_timeline if phase.default_timeline else ''
        
        phase_row_data = [
            Paragraph(f"<b>{phase_details}</b>", styles['PTPhaseCell']),
            Paragraph(f"<b>{phase_name}</b>", styles['PTPhaseCell']),
            Paragraph(f"<b>{phase_timeline}</b>", styles['PTPhaseCell']),
            '',
            ''
        ]
        table_data.append(phase_row_data)
        
        # Phase row styling
        table_style.append(
            ('BACKGROUND', (0, current_row_index), (-1, current_row_index), COLORS['phase_bg'])
        )
        current_row_index += 1

        # --------------------------------------------------------
        # TASK ROWS (White background)
        # --------------------------------------------------------
        task_list = list(phase.tasks.all())
        
        for idx, task in enumerate(task_list):
            sl_no = task.sl_no if task.sl_no else str(idx + 1)
            
            description = task.description or ''
            description = description.replace('\n', '<br/>')
            
            timeline_date = task.timeline_date.strftime('%d/%m/%Y') if task.timeline_date else ''
            invoices = task.invoices_submitted if task.invoices_submitted else ''
            amount_date = task.amount_received_date.strftime('%d/%m/%Y') if task.amount_received_date else ''
            
            task_row_data = [
                Paragraph(sl_no, styles['PTTableCellCenter']),
                Paragraph(description, styles['PTTableCell']),
                Paragraph(timeline_date, styles['PTTableCell']),
                Paragraph(invoices, styles['PTTableCellCenter']),
                Paragraph(amount_date, styles['PTTableCell']),
            ]
            table_data.append(task_row_data)
            
            # White background for task rows
            table_style.append(
                ('BACKGROUND', (0, current_row_index), (-1, current_row_index), COLORS['row_white'])
            )
            current_row_index += 1

    # Create table with repeat header on new pages
    milestone_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    milestone_table.setStyle(TableStyle(table_style))
    story.append(milestone_table)

    # --- BUILD PDF ---
    doc.build(story, canvasmaker=NumberedCanvas)

    buf.seek(0)
    filename = f"Milestone_Tracking_{project.title.replace(' ', '_')}.pdf"
    return FileResponse(buf, as_attachment=True, filename=filename)

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
        # Determine which customer form was submitted
        form_type = request.POST.get('form_type')
        
        project_form = ProjectForm(request.POST)
        formset = ProjectItemFormSet(request.POST, prefix='items') # Add a prefix
        
        customer_to_use = None
        
        if form_type == 'existing':
            existing_customer_form = ExistingCustomerForm(request.POST)
            new_customer_form = CustomerForm() # Keep an empty one for the template
            if existing_customer_form.is_valid():
                customer_to_use = existing_customer_form.cleaned_data['customer']
        else: # form_type == 'new'
            new_customer_form = CustomerForm(request.POST)
            existing_customer_form = ExistingCustomerForm() # Keep empty
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

        # Now, validate the project and item forms
        if customer_to_use and project_form.is_valid() and formset.is_valid():
            # Save the project, linking the customer
            project = project_form.save(commit=False)
            project.customer = customer_to_use
            project.save()
            
            # Save the ManyToMany field (assigned_scos)
            project_form.save_m2m()

            # Save the project items
            formset.instance = project
            formset.save()
            
            # Create the milestone phases for the new project
            MilestonePhase.objects.create(project=project, name="Kick off meeting", details="Phase 1- Module 1 & 2", default_timeline="1-3 days", order=10)
            MilestonePhase.objects.create(project=project, name="Concept Design", details="Phase 2- Module 3,4 & 5", default_timeline="4 weeks", order=20)
            MilestonePhase.objects.create(project=project, name="Detail Design", details="Phase 3- Module 6,7& 8", default_timeline="3 weeks", order=30)
            MilestonePhase.objects.create(project=project, name="Estimation", details="Phase 4", order=40)
            # ... (add the other MilestonePhase.objects.create lines) ...

            messages.success(request, 'Direct project created successfully!')
            return redirect('projects:project_detail', pk=project.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    
    else: # GET request
        existing_customer_form = ExistingCustomerForm()
        new_customer_form = CustomerForm()
        project_form = ProjectForm()
        formset = ProjectItemFormSet(queryset=ProjectItem.objects.none(), prefix='items') # Add prefix

    context = {
        'existing_customer_form': existing_customer_form,
        'new_customer_form': new_customer_form,
        'project_form': project_form,
        'formset': formset,
    }
    return render(request, 'projects/project_create_direct_form.html', context)



@login_required
@role_required('admin')
def import_fitout_items(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # We must ensure this project was created from a quotation
    if not project.quotation:
        messages.error(request, 'This project was not created from a quotation and has no items to import.')
        return redirect('projects:project_edit', pk=project.pk)
        
    # Find the associated FITOUT quotation from the same enquiry
    try:
        fitout_quote = Quotation.objects.get(
            enquiry=project.quotation.enquiry,
            quote_type='FITOUT'
        )
    except Quotation.DoesNotExist:
        messages.warning(request, 'No corresponding Fitout quotation was found for this project to import from.')
        return redirect('projects:project_edit', pk=project.pk)

    # Only proceed on a POST request for safety
    if request.method == 'POST':
        items_copied_count = 0
        for item in fitout_quote.items.all():
            # For safety, check if an identical item already exists
            if not ProjectItem.objects.filter(project=project, description=item.description).exists():
                ProjectItem.objects.create(
                    project=project,
                    description=item.description,
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=item.unit_price
                )
                items_copied_count += 1
        
        if items_copied_count > 0:
            messages.success(request, f'{items_copied_count} item(s) were successfully copied from the Fitout quotation.')
        else:
            messages.info(request, 'No new items to copy. The project scope may already be up to date.')

    # Always redirect back to the edit page
    return redirect('projects:project_edit', pk=project.pk)






@login_required
@role_required('admin')
def project_delete(request, pk):
    """Handles the confirmation and deletion of a project."""
    project = get_object_or_404(Project, pk=pk)
    
    # SAFETY CHECK: Prevent deletion if invoices exist.
    if project.invoices.exists():
        messages.error(request, f"Cannot delete '{project.title}' because it has invoices linked to it. Consider changing its status to 'Cancelled' instead.")
        return redirect('projects:project_detail', pk=project.pk)
        
    if request.method == 'POST':
        project_title = project.title
        project.delete()
        messages.warning(request, f"Project '{project_title}' and all its related tasks and reports have been permanently deleted.")
        return redirect('projects:dashboard') # Redirect to the main project list
        
    context = {'project': project}
    return render(request, 'projects/project_confirm_delete.html', context)