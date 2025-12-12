# reports/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from projects.models import Project
from .models import DailyReport
from .forms import DailyReportForm, ManpowerLogFormSet, SubcontractorLogFormSet, EquipmentLogFormSet

@login_required
def dpr_list(request, project_pk):
    """Lists all DPRs for a specific project."""
    project = get_object_or_404(Project, pk=project_pk)
    reports = DailyReport.objects.filter(project=project)
    context = {'project': project, 'reports': reports}
    return render(request, 'reports/dpr_list.html', context)

@login_required
def dpr_create_edit(request, pk=None, project_pk=None):
    """
    Handles both creating a new DPR and editing an existing one,
    along with its three related formsets.
    """
    if pk:
        report = get_object_or_404(DailyReport, pk=pk)
        project = report.project
        action = "Edit"
    else:
        report = None
        project = get_object_or_404(Project, pk=project_pk)
        action = "Create"

    if request.method == 'POST':
        form = DailyReportForm(request.POST, instance=report)

                # --- THIS IS THE FIX ---
        # If we are creating a new report, check for duplicates first.
        if not report: # This means action == "Create"
            if form.is_valid():
                report_date = form.cleaned_data.get('date')
                if DailyReport.objects.filter(project=project, date=report_date).exists():
                    messages.error(request, f"A Daily Progress Report for this project on {report_date.strftime('%d %B %Y')} already exists.")
                    # Redirect back to the list page where they can see the existing report
                    return redirect('reports:dpr_list', project_pk=project.pk)
                

        # Add prefixes to distinguish the formsets in the POST data
        manpower_formset = ManpowerLogFormSet(request.POST, instance=report, prefix='manpower')
        subcontractor_formset = SubcontractorLogFormSet(request.POST, instance=report, prefix='subcontractor')
        equipment_formset = EquipmentLogFormSet(request.POST, instance=report, prefix='equipment')
        
        # Validate all forms at once
        if form.is_valid() and manpower_formset.is_valid() and subcontractor_formset.is_valid() and equipment_formset.is_valid():
            new_report = form.save(commit=False)
            if not report: # If creating a new report
                new_report.project = project
                new_report.created_by = request.user
            new_report.save()

            # Save the formsets, linking them to the new report
            manpower_formset.instance = new_report
            manpower_formset.save()
            
            subcontractor_formset.instance = new_report
            subcontractor_formset.save()
            
            equipment_formset.instance = new_report
            equipment_formset.save()
            
            messages.success(request, f"Daily Progress Report #{new_report.report_number} saved successfully.")
            return redirect('reports:dpr_list', project_pk=project.pk)
        else:
            messages.error(request, "Please correct the errors below.")

    else: # GET request
        form = DailyReportForm(instance=report)
        # Add prefixes for the GET request as well
        manpower_formset = ManpowerLogFormSet(instance=report, prefix='manpower')
        subcontractor_formset = SubcontractorLogFormSet(instance=report, prefix='subcontractor')
        equipment_formset = EquipmentLogFormSet(instance=report, prefix='equipment')

    context = {
        'form': form,
        'manpower_formset': manpower_formset,
        'subcontractor_formset': subcontractor_formset,
        'equipment_formset': equipment_formset,
        'project': project,
        'report': report,
        'action': action,
    }
    return render(request, 'reports/dpr_form.html', context)

# Placeholder for the PDF view
# --- ADD/VERIFY THESE PDF IMPORTS AT THE TOP OF THE FILE ---
import io
import requests
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse

# Models
from .models import DailyReport 
from invoices.pdf_utils import NumberedCanvas 

# ReportLab Imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

# Image Processing Imports
from PIL import Image as PILImage, ImageOps

@login_required
def dpr_pdf_view(request, pk):
    """Generates a professional PDF with an inverted logo at top-left."""
    report = get_object_or_404(DailyReport, pk=pk)
    project = report.project
    
    buf = io.BytesIO()

    # --- 1. PAGE SETUP ---
    PAGE_SIZE = A4
    LEFT_MARGIN = 0.5 * inch
    RIGHT_MARGIN = 0.5 * inch
    TOP_MARGIN = 0.5 * inch
    BOTTOM_MARGIN = 0.8 * inch
    doc_width = PAGE_SIZE[0] - (LEFT_MARGIN + RIGHT_MARGIN)

    doc = SimpleDocTemplate(buf, pagesize=PAGE_SIZE,
                            rightMargin=RIGHT_MARGIN, leftMargin=LEFT_MARGIN,
                            topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN)
    
    # --- 2. STYLES ---
    styles = getSampleStyleSheet()
    
    # Title Style (Aligned Left/Center depending on preference, here Center of its cell)
    style_title = ParagraphStyle(name='ReportTitle', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16, spaceAfter=0)
    
    # Table Styles
    style_th = ParagraphStyle(name='TableHeader', fontName='Helvetica-Bold', fontSize=8, alignment=TA_CENTER)
    style_td_left = ParagraphStyle(name='TableCellLeft', fontName='Helvetica', fontSize=8, alignment=TA_LEFT, leading=10)
    style_td_center = ParagraphStyle(name='TableCellCenter', fontName='Helvetica', fontSize=8, alignment=TA_CENTER)
    style_section = ParagraphStyle(name='SectionTitle', parent=styles['Heading3'], fontSize=10, spaceBefore=6, textColor=colors.black)

    story = []

    # --- 3. LOGO & TITLE HEADER ---
    logo_url = "https://curvacraft.com/wp-content/uploads/2024/10/Curvacraft-logo-1024x255.webp"
    logo_img = None
    
    try:
        # Fetch Image
        response = requests.get(logo_url, stream=True)
        response.raise_for_status()
        
        # Open with PIL
        pil_img = PILImage.open(io.BytesIO(response.content))
        
        # Handle Inversion (Preserving Transparency)
        if pil_img.mode == 'RGBA':
            r, g, b, a = pil_img.split()
            rgb_image = PILImage.merge('RGB', (r, g, b))
            inverted_image = ImageOps.invert(rgb_image) # Invert Colors
            r2, g2, b2 = inverted_image.split()
            pil_img = PILImage.merge('RGBA', (r2, g2, b2, a)) # Merge back Alpha
        else:
            pil_img = ImageOps.invert(pil_img.convert('RGB'))
            
        # Convert to PNG for ReportLab buffer
        img_buffer = io.BytesIO()
        pil_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Calculate Aspect Ratio for ReportLab
        # Original: 1024x255. Desired Width: ~2 inches
        aspect = 255.0 / 1024.0
        display_width = 2.0 * inch
        display_height = display_width * aspect
        
        logo_img = RLImage(img_buffer, width=display_width, height=display_height)
        logo_img.hAlign = 'LEFT'

    except Exception as e:
        print(f"Logo fetch error: {e}")
        logo_img = Paragraph("<b>[LOGO ERROR]</b>", style_td_left)

    # Create Top Header Table: [Logo] | [Title]
    # We give the logo column enough space, and the title takes the rest.
    title_para = Paragraph("DAILY PROGRESS REPORT", style_title)
    
    # Table Layout: Logo (30%), Title (70%)
    top_table = Table([[logo_img, title_para]], colWidths=[doc_width*0.35, doc_width*0.65])
    top_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), # Vertically align logo and text
        ('ALIGN', (0,0), (0,0), 'LEFT'),      # Align Logo Left
        ('ALIGN', (1,0), (1,0), 'CENTER'),    # Align Title Center
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(top_table)
    story.append(Spacer(1, 0.2*inch))

    # ------------------------------------------------------------------
    # 4. PROJECT INFO & TIMELINE (Standard Content)
    # ------------------------------------------------------------------
    
    def clean_str(val): return str(val) if val is not None else "N/A"
    def clean_date(val): return val.strftime('%d-%b-%y') if val else "N/A"

    # Left: Info
    left_data = [
        [Paragraph('<b>PROJECT:</b>', style_td_left), Paragraph(project.title, style_td_left)],
        [Paragraph('<b>CONTRACTOR</b>',  style_td_left), Paragraph(report.contractor_name, style_td_left)],
        [Paragraph('<b>SITE ENGG:</b>', style_td_left), Paragraph(project.site_engineer if project.site_engineer else 'N/A', style_td_left)],
        [Paragraph('<b>REPORT NO:</b>', style_td_left), Paragraph(clean_str(report.report_number), style_td_left)],
        [Paragraph('<b>DATE:</b>', style_td_left), Paragraph(report.date.strftime('%d-%b-%Y'), style_td_left)],
    ]
    
    # Right: Timeline
    right_data = [
        [Paragraph('<b>PROJECT TIMELINE</b>', style_th)],
        [Paragraph(f'Start: {clean_date(project.mobilization_date)}', style_td_left)],
        [Paragraph(f'End: {clean_date(project.handover_date)}', style_td_left)],
        [Paragraph(f'Days Remaining: {clean_str(project.days_remaining)}', style_td_left)],
    ]

    col_w_left = doc_width * 0.65
    col_w_right = doc_width * 0.35

    t_left = Table(left_data, colWidths=[col_w_left * 0.3, col_w_left * 0.7])
    t_left.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))

    t_right = Table(right_data, colWidths=[col_w_right])
    t_right.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,0), colors.whitesmoke),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))

    main_header_wrapper = Table([[t_left, t_right]], colWidths=[col_w_left, col_w_right])
    main_header_wrapper.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    
    story.append(main_header_wrapper)
    story.append(Spacer(1, 0.15*inch))

    # ------------------------------------------------------------------
    # 5. MANPOWER & EQUIPMENT
    # ------------------------------------------------------------------
    story.append(Paragraph("CONTRACTOR DETAILS", style_section))
    # Manpower
    mp_data = [[Paragraph('S.No', style_th), Paragraph('MANPOWER', style_th), Paragraph('DAY', style_th), Paragraph('NGT', style_th)]]
    total_mp_day = total_mp_night = 0
    for i, item in enumerate(report.manpower_logs.all(), 1):
        mp_data.append([str(i), Paragraph(item.staff_type, style_td_left), item.day_count, item.night_count])
        total_mp_day += item.day_count; total_mp_night += item.night_count
    mp_data.append(['', Paragraph('<b>TOTAL</b>', style_td_center), total_mp_day, total_mp_night])

    # Equipment
    eq_data = [[Paragraph('S.No', style_th), Paragraph('EQUIPMENT', style_th), Paragraph('DAY', style_th), Paragraph('NGT', style_th)]]
    total_eq_day = total_eq_night = 0
    for i, item in enumerate(report.equipment_logs.all(), 1):
        eq_data.append([str(i), Paragraph(item.equipment_name, style_td_left), item.day_count, item.night_count])
        total_eq_day += item.day_count; total_eq_night += item.night_count
    eq_data.append(['',Paragraph('<b>TOTAL</b>', style_td_center), total_eq_day, total_eq_night])

    # Side by side calculation
    gap = 0.2 * inch
    half_w = (doc_width - gap) / 2
    ratios = [0.1, 0.6, 0.15, 0.15]
    
    t_mp = Table(mp_data, colWidths=[half_w * r for r in ratios])
    t_eq = Table(eq_data, colWidths=[half_w * r for r in ratios])

    common_style = TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (2,1), (-1,-1), 'CENTER'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.whitesmoke), # Footer BG
    ])
    t_mp.setStyle(common_style)
    t_eq.setStyle(common_style)

    story.append(Table([[t_mp, '', t_eq]], colWidths=[half_w, gap, half_w]))
    story.append(Spacer(1, 0.15*inch))

    # ------------------------------------------------------------------
    # 6. SUBCONTRACTORS
    # ------------------------------------------------------------------

    # --- CHANGE 1: Create a dynamic section header ---
    # If a subcontractor name exists, include it in the main header.
    if report.subcontractor_name:
        section_title = f"SUBCONTRACTOR DETAILS: {report.subcontractor_name}"
    else:
        section_title = "SUBCONTRACTOR DETAILS"
    story.append(Paragraph(section_title, style_section))


    # --- CHANGE 2: Remove the 'SUBCONTRACTOR NAME' column from the header list ---
    sub_data = [
        [Paragraph('S.No', style_th), 
        Paragraph('WORK TYPE', style_th), 
        Paragraph('DAY', style_th), 
        Paragraph('NGT', style_th)]
    ]
    t_sub_d = t_sub_n = 0

    for i, item in enumerate(report.subcontractor_logs.all(), 1):
        # --- CHANGE 3: Remove the 'subcontractor_name' data from the row ---
        sub_data.append([
            str(i), 
            Paragraph(item.staff_type, style_td_left), 
            item.day_count, 
            item.night_count
        ])
        t_sub_d += item.day_count
        t_sub_n += item.night_count

    # --- CHANGE 4: Adjust the TOTAL row ---
    # It now only needs one empty string at the beginning to align correctly.
    sub_data.append([ '', Paragraph('<b>TOTAL</b>', style_td_center), t_sub_d, t_sub_n])

    # --- CHANGE 5: Revert to your original column widths ---
    # Since we removed a column, the original widths are correct again.
    t_sub = Table(sub_data, colWidths=[0.5*inch, doc_width - 2.5*inch, 1*inch, 1*inch])

    t_sub.setStyle(common_style)
    story.append(t_sub)
    story.append(Spacer(1, 0.15*inch))

    # ------------------------------------------------------------------
    # 7. CHRONOLOGICAL & ISSUES
    # ------------------------------------------------------------------
    story.append(Paragraph("CHRONOLOGICAL ACCOUNT OF DAY'S WORK", style_section))
    chrono_txt = report.chronological_account.replace('\n', '<br/>') if report.chronological_account else "No entry."
    t_chrono = Table([[Paragraph(chrono_txt, style_td_left)]], colWidths=[doc_width])
    t_chrono.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
    story.append(t_chrono)
    story.append(Spacer(1, 0.15*inch))

    # Bottom Section
    act_txt = report.activities_for_next_day.replace('\n', '<br/>') if report.activities_for_next_day else "N/A"
    iss_txt = report.issues_encountered.replace('\n', '<br/>') if report.issues_encountered else "N/A"
    
    bot_data = [
        [Paragraph("PLANNED ACTIVITIES FOR NEXT DAY", style_th), Paragraph("ISSUES / SAFETY", style_th)],
        [Paragraph(act_txt, style_td_left), Paragraph(iss_txt, style_td_left)]
    ]
    t_bot = Table(bot_data, colWidths=[doc_width/2, doc_width/2])
    t_bot.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_bot)
    story.append(Spacer(1, 0.4*inch))

    # ------------------------------------------------------------------
    # 8. SIGNATURES
    # ------------------------------------------------------------------
    sig_data = [[Paragraph("_______________________<br/><b>Site Engineer</b>", style_td_center), 
                 Paragraph("_______________________<br/><b>Project Manager</b>", style_td_center)]]
    story.append(Table(sig_data, colWidths=[doc_width/2, doc_width/2]))

    # Build
    doc.build(story, canvasmaker=NumberedCanvas)
    
    buf.seek(0)
    filename = f"DPR_{project.title.replace(' ', '_')}_{report.date}.pdf"
    return FileResponse(buf, as_attachment=True, filename=filename)



# reports/views.py
from django.http import JsonResponse # Add this import


# --- ADD THIS NEW VIEW ---
@login_required
def ajax_check_dpr_date(request):
    # We get the data sent by the JavaScript
    project_pk = request.GET.get('project_pk')
    date_str = request.GET.get('date')

    # Check if a report exists for this project and date
    exists = DailyReport.objects.filter(project_id=project_pk, date=date_str).exists()

    # Return a JSON response
    return JsonResponse({'exists': exists})