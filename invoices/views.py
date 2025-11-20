# invoices/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from projects.models import Project
from .models import Invoice
from .forms import InvoiceForm, InvoiceItemFormSet , InvoiceStatusForm

# PDF Generation Imports
import io
import requests
from django.http import FileResponse
from .models import Invoice
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from PIL import Image as PILImage, ImageOps

# ReportLab Imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import Flowable
from reportlab.lib.utils import ImageReader

# We will reuse the PDF helper functions. Let's create a file for them.
from .pdf_utils import NumberedCanvas, process_logo, LineSeparator
# -----------------
# CORE INVOICE VIEWS
# -----------------

@login_required
def invoice_create_edit(request, pk=None, project_pk=None):
    """
    Handles both the creation of a new invoice from a project and
    the editing of an existing invoice.
    """
    if pk:
        invoice = get_object_or_404(Invoice, pk=pk)
        project = invoice.project
        action = "Edit"
    else:
        invoice = None
        project = get_object_or_404(Project, pk=project_pk)
        action = "Create"

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            new_invoice = form.save(commit=False)
            if not invoice: # If creating
                new_invoice.project = project
            new_invoice.save()

            formset.instance = new_invoice
            formset.save()
            
            messages.success(request, f'Invoice {new_invoice.invoice_number} has been saved successfully.')
            return redirect('invoices:invoice_detail', pk=new_invoice.pk)
    else:
        # For a new invoice, pre-fill the tax rate from the project
        initial_data = {'tax_percentage': project.tax_percentage} if not invoice else None
        form = InvoiceForm(instance=invoice, initial=initial_data)
        formset = InvoiceItemFormSet(instance=invoice)

    context = {
        'form': form,
        'formset': formset,
        'project': project,
        'invoice': invoice,
        'action': action,
        'project_subtotal': project.subtotal # Pass the pre-VAT amount
    }
    return render(request, 'invoices/invoice_form.html', context)

@login_required
def invoice_detail(request, pk):
    """Displays a complete overview of a single invoice and handles status updates."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # --- ADD THIS FORM HANDLING LOGIC ---
    if request.method == 'POST':
        # This POST is only for the status update
        status_form = InvoiceStatusForm(request.POST, instance=invoice)
        if status_form.is_valid():
            # Prevent changing a 'VOID' status back
            if invoice.status == 'VOID':
                messages.error(request, "A voided invoice cannot be changed.")
            else:
                status_form.save()
                messages.success(request, 'Invoice status has been updated.')
            return redirect('invoices:invoice_detail', pk=invoice.pk)
    else:
        status_form = InvoiceStatusForm(instance=invoice)

    context = {
        'invoice': invoice,
        'status_form': status_form # Add the form to the context
    }
    return render(request, 'invoices/invoice_detail.html', context)

@login_required
def invoice_void(request, pk):
    """Handles the confirmation and action of voiding an invoice."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        # Check that the invoice is not already void to prevent multi-submissions
        if invoice.status != 'VOID':
            invoice.status = 'VOID'
            invoice.save()
            messages.warning(request, f"Invoice {invoice.invoice_number} has been voided.")
        else:
            messages.info(request, "This invoice has already been voided.")
        return redirect('projects:project_detail', pk=invoice.project.pk)
    
    return render(request, 'invoices/invoice_confirm_void.html', {'invoice': invoice})

# -----------------
# PDF VIEW
# -----------------

# invoices/views.py

# ... (all your other imports should be at the top) ...
from datetime import timedelta # Make sure this is imported

# ... (your other views like invoice_create_edit, etc.) ...


# ---------------------------------
# THE COMPLETE AND CORRECT INVOICE PDF VIEW
# ---------------------------------
@login_required
def invoice_pdf_view(request, pk):
    """Generates a professional, beautifully designed PDF Invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    buf = io.BytesIO()

    # --- SETUP DOCUMENT ---
    doc = SimpleDocTemplate(
        buf, 
        pagesize=letter,
        rightMargin=0.75*inch, 
        leftMargin=0.75*inch,
        topMargin=1.2*inch, 
        bottomMargin=1.5*inch,
        title=f"Invoice {invoice.invoice_number}",
        author="CURVACRAFT DESIGN & BUILD STUDIO"
    )
    
    content_width = doc.width

    # --- PROFESSIONAL COLOR PALETTE & STYLES ---
    primary_color = colors.HexColor("#2C3E50")
    accent_color = colors.HexColor("#9d9084")
    secondary_color = colors.HexColor("#7F8C8D")
    light_gray = colors.HexColor("#ECF0F1")
    border_color = colors.HexColor("#BDC3C7")
    header_bg = colors.HexColor("#34495E")
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CompanyName', fontName='Helvetica-Bold', fontSize=24, textColor=primary_color, spaceAfter=6, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='QuotationTitle', fontName='Helvetica-Bold', fontSize=18, textColor=accent_color, alignment=TA_RIGHT, spaceAfter=12))
    styles.add(ParagraphStyle(name='SectionHeader', fontName='Helvetica-Bold', fontSize=13, textColor=primary_color, spaceBefore=12, spaceAfter=8, borderColor=accent_color, borderWidth=2, borderPadding=3, leftIndent=0))
    styles.add(ParagraphStyle(name='ContactInfo', fontName='Helvetica', fontSize=9, textColor=secondary_color, leading=12))
    styles.add(ParagraphStyle(name='ClientInfo', fontName='Helvetica', fontSize=10, textColor=primary_color, leading=14))
    styles.add(ParagraphStyle(name='TableHeader', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='TableCell', fontName='Helvetica', fontSize=9, textColor=primary_color, leading=12))
    styles.add(ParagraphStyle(name='TableCellRight', fontName='Helvetica', fontSize=9, textColor=primary_color, alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='TableCellBoldRight', fontName='Helvetica-Bold', fontSize=9, textColor=primary_color, alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='TotalLabel', fontName='Helvetica', fontSize=11, textColor=secondary_color, alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='TotalValue', fontName='Helvetica-Bold', fontSize=11, textColor=primary_color, alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='GrandTotal', fontName='Helvetica-Bold', fontSize=13, textColor=accent_color, alignment=TA_RIGHT))

    # --- BUILD STORY ---
    story = []

    # 1. HEADER
    logo_url = "https://curvacraft.com/wp-content/uploads/2024/10/Curvacraft-logo-1024x255.webp"
    logo = process_logo(logo_url)
    if not logo:
        logo = Paragraph("<b>CURVACRAFT</b>", styles['Normal'])

    invoice_info_html = f"""
        <font size='14' color='#{accent_color.hexval()[2:]}'><b>INVOICE</b></font><br/>
        <font size='9' color='#{secondary_color.hexval()[2:]}'>#{invoice.invoice_number}</font><br/>
        <font size='9' color='#{secondary_color.hexval()[2:]}'>{invoice.date:%d %B %Y}</font>
    """
    header_table = Table([[logo, Paragraph(invoice_info_html, styles['QuotationTitle'])]], colWidths=[content_width - 2.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
    
    story.append(header_table)
    story.append(Spacer(1, 0.2*inch))
    story.append(LineSeparator(content_width, 2, accent_color))
    story.append(Spacer(1, 0.3*inch))
    
    # 2. CLIENT & COMPANY INFO
    client_info = f"""
        <font color='#{accent_color.hexval()[2:]}' size='11'><b>INVOICE TO</b></font><br/>
        <font size='10'><b>{invoice.project.customer.name}</b></font><br/>
        {invoice.project.customer.email or ''}<br/>
        {invoice.project.customer.phone_number or ''}
    """
    company_info = f"""
        <font color='#{accent_color.hexval()[2:]}' size='11'><b>FROM</b></font><br/>
        <font size='10'><b>CURVACRAFT DESIGN & BUILD STUDIO</b></font><br/>
        Studio Management Division<br/>
        info@curvacraft.com<br/>
        www.curvacraft.com
    """
    info_table = Table([[Paragraph(client_info, styles['ClientInfo']), Paragraph(company_info, styles['ClientInfo'])]], colWidths=[content_width / 2, content_width / 2])
    info_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), light_gray), ('BOX', (0,0), (-1,-1), 1, border_color), ('PADDING', (0,0), (-1,-1), 12)]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*inch))
    
    # 3. INVOICE DETAILS
    invoice_details_html = f"<font color='#{secondary_color.hexval()[2:]}'><b>Project:</b></font> {invoice.project.title}<br/>"
    if invoice.due_date:
        invoice_details_html += f"<font color='#{secondary_color.hexval()[2:]}'><b>Due Date:</b></font> {invoice.due_date:%d %B %Y}"
    story.append(Paragraph(invoice_details_html, styles['ClientInfo']))
    story.append(Spacer(1, 0.3*inch))
    
    # 4. LINE ITEMS
    story.append(Paragraph("BILLING DETAILS", styles['SectionHeader']))
    story.append(Spacer(1, 0.15*inch))
    
    table_header = [Paragraph(h, styles['TableHeader']) for h in ['S/N', 'DESCRIPTION', 'QTY / %', 'TYPE', 'BASIS AMOUNT', 'TOTAL']]
    table_data = [table_header]
    
    for i, item in enumerate(invoice.items.all(), 1):
        row_data = [
            Paragraph(str(i), styles['TableCell']), Paragraph(item.description or '', styles['TableCell']),
            Paragraph(f"{item.quantity:,.2f}", styles['TableCellRight']), Paragraph(item.get_quantity_type_display(), styles['TableCell']),
            Paragraph(f"AED {item.unit_price:,.2f}", styles['TableCellRight']), Paragraph(f"AED {item.total_amount:,.2f}", styles['TableCellBoldRight'])
        ]
        table_data.append(row_data)
        
    items_table = Table(table_data, colWidths=[0.4*inch, 3.2*inch, 0.6*inch, 0.6*inch, 1.0*inch, 1.2*inch], repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), header_bg), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color), ('BOX', (0,0), (-1,-1), 1.5, primary_color),
        ('PADDING', (0,0), (-1,-1), 8), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,1), (0,-1), 'CENTER'), ('ALIGN', (2,1), (2,-1), 'RIGHT'), ('ALIGN', (4,1), (5,-1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_gray]),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.3*inch))
    
    # 5. FINANCIAL SUMMARY
    summary_data = [
        [Paragraph('Subtotal:', styles['TotalLabel']), Paragraph(f"AED {invoice.subtotal:,.2f}", styles['TotalValue'])],
        [Paragraph(f'VAT ({invoice.tax_percentage}%):', styles['TotalLabel']), Paragraph(f"AED {invoice.tax_amount:,.2f}", styles['TotalValue'])],
        [Spacer(1, 0.1*inch), Spacer(1, 0.1*inch)],
        [Paragraph('<b>GRAND TOTAL:</b>', styles['GrandTotal']), Paragraph(f'<b>AED {invoice.grand_total:,.2f}</b>', styles['GrandTotal'])]
    ]
    summary_table = Table(summary_data, colWidths=[1.8*inch, 1.5*inch])
    summary_table.hAlign = 'RIGHT'
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,3), (-1,3), light_gray), ('BOX', (0,3), (-1,3), 1.5, accent_color), ('PADDING', (0,3), (-1,3), 12),
        ('LINEABOVE', (0,3), (-1,3), 2, primary_color),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*inch))
    
    # 6. PAYMENT INFORMATION
    story.append(Paragraph("PAYMENT INFORMATION", styles['SectionHeader']))
    story.append(Spacer(1, 0.1*inch))
    payment_text = """
    <b>Account Name:</b> Curvacraft Decoration Design LLC<br/>
    <b>Bank Name:</b> ADCB<br/>
    <b>Account No:</b> 13918074910001<br/>
    <b>IBAN:</b> AE660030013918074910001<br/>
    <b>Swift Code:</b> ADCBAEAA
    """
    payment_para = Paragraph(payment_text, styles['TableCell'])
    payment_box = Table([[payment_para]], colWidths=[content_width])
    payment_box.setStyle(TableStyle([('BACKGROUND', (0,0), (0,0), light_gray), ('BOX', (0,0), (0,0), 1, border_color), ('PADDING', (0,0), (-1,-1), 15)]))
    story.append(KeepTogether(payment_box))
    story.append(Spacer(1, 0.4*inch))

    # 7. THANK YOU NOTE
    thank_you_html = f"""<para align='center'><font color='#{accent_color.hexval()[2:]}' size='12'><b>Thank you for your business!</b></font></para>"""
    story.append(Paragraph(thank_you_html, styles['BodyText']))
    
    # --- BUILD THE PDF ---
    doc.build(story, canvasmaker=NumberedCanvas)
    
    # --- RETURN THE RESPONSE ---
    buf.seek(0)
    filename = f"Invoice_{invoice.invoice_number}_{invoice.project.customer.name.replace(' ', '_')}.pdf"
    return FileResponse(buf, as_attachment=True, filename=filename)