# quotations/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from enquiries.models import Enquiry
from .models import Quotation
from .forms import QuotationForm, QuotationItemFormSet, QuotationStatusForm
from users.decorators import role_required
# PDF Generation Imports
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

# -----------------
# CORE VIEWS
# -----------------
@role_required('admin','staff')
@login_required
def quotation_list(request):
    """
    Displays a list of all ENQUIRIES that are ready for quotations,
    and provides links to manage their Design and Fitout quotes.
    """
    enquiries_with_quotes = Enquiry.objects.filter(
        status__in=['QUALIFIED', 'REJECTED']
    ).prefetch_related('quotations').order_by('-created_at')

    # --- NEW LOGIC: Process the enquiries to attach specific quotes ---
    for enquiry in enquiries_with_quotes:
        # Initialize attributes to None
        enquiry.design_quote = None
        enquiry.fitout_quote = None
        # Loop through the prefetched quotations for this enquiry
        for quote in enquiry.quotations.all():
            if quote.quote_type == 'DESIGN':
                enquiry.design_quote = quote
            elif quote.quote_type == 'FITOUT':
                enquiry.fitout_quote = quote
    
    context = {'enquiries': enquiries_with_quotes}
    return render(request, 'quotations/quotation_list.html', context)

@role_required('admin','staff')
@login_required
def quotation_detail(request, pk):
    """Displays the details, line items, and status form for a single quotation."""
    quotation = get_object_or_404(Quotation, pk=pk)
    status_form = QuotationStatusForm(instance=quotation)

    if request.method == 'POST':
        status_form = QuotationStatusForm(request.POST, instance=quotation)
        if status_form.is_valid():
            status_form.save()
            messages.success(request, 'Quotation status has been updated.')
            return redirect('quotations:quotation_detail', pk=quotation.pk)

    context = {'quotation': quotation, 'status_form': status_form}
    return render(request, 'quotations/quotation_detail.html', context)

@role_required('admin','staff')
@login_required
def manage_quotation(request, enquiry_pk, quote_type):
    """
    The main view for creating AND editing a quotation.
    It finds an existing quote of the correct type or prepares for creation.
    """
    enquiry = get_object_or_404(Enquiry, pk=enquiry_pk)
    quotation = Quotation.objects.filter(enquiry=enquiry, quote_type=quote_type).first()
    
    action = "Edit" if quotation else "Create"

    if request.method == 'POST':
        form = QuotationForm(request.POST, instance=quotation)
        formset = QuotationItemFormSet(request.POST, instance=quotation)
        
        if form.is_valid() and formset.is_valid():
            new_quote = form.save(commit=False)
            if not quotation: # We are creating a new quote
                new_quote.enquiry = enquiry
                new_quote.quote_type = quote_type
            new_quote.save()
            
            formset.instance = new_quote
            formset.save()
            
            if enquiry.status == 'PENDING':
                enquiry.status = 'QUALIFIED'
                enquiry.save()
                
            messages.success(request, f'{quote_type.capitalize()} quotation saved successfully.')
            return redirect('quotations:quotation_detail', pk=new_quote.pk)
    else:
        form = QuotationForm(instance=quotation)
        formset = QuotationItemFormSet(instance=quotation)

    context = {
        'form': form,
        'formset': formset,
        'enquiry': enquiry,
        'quote_type': quote_type,
        'action': action
    }
    return render(request, 'quotations/quotation_form.html', context)

# -----------------
# PDF VIEW
# -----------------

# --- ADD ALL OF THESE NEW IMPORTS AT THE TOP OF THE FILE ---
# --- ADD/VERIFY ALL OF THESE NEW IMPORTS AT THE TOP OF THE FILE ---
# -----------------
# PDF VIEW
# -----------------

# --- ADD ALL OF THESE NEW IMPORTS AT THE TOP OF THE FILE ---
# --- ADD/VERIFY ALL OF THESE NEW IMPORTS AT THE TOP OF THE FILE ---
import io
import requests
from django.http import FileResponse
from .models import Quotation
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from PIL import Image as PILImage, ImageOps
import numpy as np
from datetime import timedelta
# ReportLab Imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.graphics.shapes import Drawing, Line, Rect
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import Flowable
from reportlab.lib.utils import ImageReader


# ---------------------------------
# CUSTOM LINE SEPARATOR
# ---------------------------------
class LineSeparator(Flowable):
    """Custom line separator with color control"""
    def __init__(self, width, height=1, color=colors.HexColor("#E0E0E0")):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color
        
    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.height)
        self.canv.line(0, 0, self.width, 0)

# ---------------------------------
# PDF PAGE NUMBER HELPER CLASS
# ---------------------------------
class NumberedCanvas(canvas.Canvas):
    """Enhanced canvas with professional footer and image watermark"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self._watermark_image = self._get_watermark_image()

    def _get_watermark_image(self):
        """Downloads, inverts, and prepares the logo for watermarking."""
        logo_url = "https://curvacraft.com/wp-content/uploads/2024/10/Curvacraft-logo-1024x255.webp"
        try:
            response = requests.get(logo_url, stream=True, timeout=5)
            if response.status_code == 200:
                pil_img = PILImage.open(io.BytesIO(response.content))
                
                if pil_img.mode != 'RGBA':
                    pil_img = pil_img.convert('RGBA')
                
                # Invert colors while preserving alpha
                r, g, b, a = pil_img.split()
                rgb_image = PILImage.merge('RGB', (r, g, b))
                inverted_rgb = ImageOps.invert(rgb_image)
                inverted_r, inverted_g, inverted_b = inverted_rgb.split()
                inverted_image = PILImage.merge('RGBA', (inverted_r, inverted_g, inverted_b, a))
                
                img_buffer = io.BytesIO()
                inverted_image.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                return ImageReader(img_buffer)
        except Exception as e:
            print(f"Watermark image processing error: {e}")
        return None

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
        
        # Draw watermark on the new page before any content
        if self._watermark_image:
            self.saveState()
            self.setFillAlpha(0.08) # Set opacity to 8%
            # Center the watermark on the page
            img_width, img_height = self._watermark_image.getSize()
            aspect = img_height / float(img_width)
            display_width = 6 * inch
            display_height = display_width * aspect
            
            x_centered = (letter[0] - display_width) / 2
            y_centered = (letter[1] - display_height) / 2
            
            self.drawImage(
                self._watermark_image, 
                x_centered, 
                y_centered, 
                width=display_width, 
                height=display_height,
                mask='auto' # Handles transparency
            )
            self.restoreState()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        
        # Footer background
        self.setFillColor(colors.HexColor("#FAFAFA"))
        self.rect(0, 0, letter[0], 1.2*inch, fill=1, stroke=0)
        
        # Footer line
        self.setStrokeColor(colors.HexColor("#D0D0D0"))
        self.setLineWidth(0.5)
        self.line(0.75*inch, 1.1*inch, letter[0] - 0.75*inch, 1.1*inch)
        
        # Footer text
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#757575"))
        
        # Page number
        self.drawRightString(letter[0] - 0.75*inch, 0.85*inch, f"Page {self._pageNumber} of {page_count}")
        
        # Company details - left side
        self.drawString(0.75*inch, 0.85*inch, "CURVACRAFT DESIGN & BUILD STUDIO")
        self.drawString(0.75*inch, 0.65*inch, "info@curvacraft.com | www.curvacraft.com")
        self.drawString(0.75*inch, 0.45*inch, "Dubai, United Arab Emirates")
        
        self.restoreState()


# ---------------------------------
# LOGO PROCESSING FUNCTION
# ---------------------------------
def process_logo(logo_url):
    """Download and invert logo colors for the header."""
    try:
        response = requests.get(logo_url, stream=True, timeout=5)
        if response.status_code == 200:
            # Open image with PIL
            pil_img = PILImage.open(io.BytesIO(response.content))
            
            # Convert to RGBA if not already
            if pil_img.mode != 'RGBA':
                pil_img = pil_img.convert('RGBA')
            
            # Invert colors while preserving alpha
            r, g, b, a = pil_img.split()
            rgb_image = PILImage.merge('RGB', (r, g, b))
            inverted_rgb = ImageOps.invert(rgb_image)
            inverted_r, inverted_g, inverted_b = inverted_rgb.split()
            inverted_image = PILImage.merge('RGBA', (inverted_r, inverted_g, inverted_b, a))
            
            # Save to BytesIO
            img_buffer = io.BytesIO()
            inverted_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return Image(img_buffer, width=2.8*inch, height=0.7*inch)
    except Exception as e:
        print(f"Header logo processing error: {e}")
    
    return None

# ---------------------------------
# THE ENHANCED PDF VIEW
# ---------------------------------
@login_required
@role_required('admin','staff')
def quotation_pdf_view(request, pk):
    """Generates a professional, beautifully designed PDF quotation"""
    quotation = get_object_or_404(Quotation, pk=pk)
    
    buf = io.BytesIO()

    # --- SETUP DOCUMENT ---
    doc = SimpleDocTemplate(
        buf, 
        pagesize=letter,
        rightMargin=0.75*inch, 
        leftMargin=0.75*inch,
        topMargin=1.2*inch, 
        bottomMargin=1.5*inch,
        title=f"Quotation {quotation.quotation_number}",
        author="CURVACRAFT DESIGN & BUILD STUDIO"
    )
    
    # --- NEW: DEFINE CONTENT WIDTH FOR ALIGNMENT ---
    content_width = doc.width

    # --- PROFESSIONAL COLOR PALETTE ---
    primary_color = colors.HexColor("#2C3E50")      # Dark blue-gray
    accent_color = colors.HexColor("#9d9084")       # Golden accent
    secondary_color = colors.HexColor("#7F8C8D")    # Medium gray
    light_gray = colors.HexColor("#ECF0F1")         # Very light gray
    border_color = colors.HexColor("#BDC3C7")       # Border gray
    header_bg = colors.HexColor("#34495E")          # Dark header
    
    # --- ENHANCED STYLES ---
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(
        name='CompanyName',
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=primary_color,
        spaceAfter=6,
        alignment=TA_LEFT
    ))
    
    styles.add(ParagraphStyle(
        name='QuotationTitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=accent_color,
        alignment=TA_RIGHT,
        spaceAfter=12
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=8,
        borderColor=accent_color,
        borderWidth=2,
        borderPadding=3,
        leftIndent=0
    ))
    
    styles.add(ParagraphStyle(
        name='ContactInfo',
        fontName='Helvetica',
        fontSize=9,
        textColor=secondary_color,
        leading=12
    ))
    
    styles.add(ParagraphStyle(
        name='ClientInfo',
        fontName='Helvetica',
        fontSize=10,
        textColor=primary_color,
        leading=14
    ))
    
    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=9,
        textColor=primary_color,
        leading=12
    ))
    
    styles.add(ParagraphStyle(
        name='TableCellRight',
        fontName='Helvetica',
        fontSize=9,
        textColor=primary_color,
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='TableCellBoldRight',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=primary_color,
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='TotalLabel',
        fontName='Helvetica',
        fontSize=11,
        textColor=secondary_color,
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='TotalValue',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=primary_color,
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='GrandTotal',
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=accent_color,
        alignment=TA_RIGHT
    ))

    # --- BUILD STORY ---
    story = []

    # 1. PROFESSIONAL HEADER WITH LOGO
    logo_url = "https://curvacraft.com/wp-content/uploads/2024/10/Curvacraft-logo-1024x255.webp"
    logo = process_logo(logo_url)
    
    if not logo:
        logo = Paragraph("<b>CURVACRAFT</b><br/><font size='8'>DESIGN & BUILD STUDIO</font>", styles['CompanyName'])
    
    # Header table with logo and quotation info
    quote_info = f"""
        <font size='14' color='#{accent_color.hexval()[2:]}'><b>QUOTATION</b></font><br/>
        <font size='9' color='#{secondary_color.hexval()[2:]}'>#{quotation.quotation_number}</font><br/>
        <font size='9' color='#{secondary_color.hexval()[2:]}'>{quotation.created_at:%d %B %Y}</font>
    """
    
    header_data = [[
        logo,
        Paragraph(quote_info, styles['QuotationTitle'])
    ]]
    
    # MODIFIED: Adjusted header table to use content_width
    header_table = Table(header_data, colWidths=[content_width - 2.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 0.2*inch))
    # MODIFIED: Line separator now uses full content_width
    story.append(LineSeparator(content_width, 2, accent_color))
    story.append(Spacer(1, 0.3*inch))
    
    # 2. CLIENT AND COMPANY INFORMATION
    # Create two-column layout for client and company info
    client_info = f"""
        <font color='#{accent_color.hexval()[2:]}' size='11'><b>CLIENT DETAILS</b></font><br/>
        <font size='10'><b>{quotation.enquiry.customer.name}</b></font><br/>
        """
    
    if quotation.enquiry.customer.email:
        client_info += f"{quotation.enquiry.customer.email}<br/>"
    if quotation.enquiry.customer.phone_number:
        client_info += f"{quotation.enquiry.customer.phone_number}<br/>"
    if hasattr(quotation.enquiry.customer, 'address') and quotation.enquiry.customer.address:
        client_info += f"{quotation.enquiry.customer.address}"
    
    company_info = f"""
        <font color='#{accent_color.hexval()[2:]}' size='11'><b>FROM</b></font><br/>
        <font size='10'><b>CURVACRAFT DESIGN & BUILD STUDIO</b></font><br/>
        Studio Management Division<br/>
        info@curvacraft.com<br/>
        www.curvacraft.com
    """
    
    info_data = [[
        Paragraph(client_info, styles['ClientInfo']),
        Paragraph(company_info, styles['ClientInfo'])
    ]]
    
    # MODIFIED: Info table columns are now half of the content_width each for perfect justification
    info_table = Table(info_data, colWidths=[content_width / 2, content_width / 2])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), light_gray),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.4*inch))
    
    # 3. QUOTATION DETAILS SECTION
    quote_details = f"""
        <font color='#{secondary_color.hexval()[2:]}'><b>Quote Type:</b></font> {quotation.get_quote_type_display()}<br/>
        <font color='#{secondary_color.hexval()[2:]}'><b>Valid Until:</b></font> {(quotation.created_at + timedelta(days=30)):%d %B %Y}<br/>
        <font color='#{secondary_color.hexval()[2:]}'><b>Payment Terms:</b></font> 50% Advance, 50% on Completion
    """
    
    details_para = Paragraph(quote_details, styles['ClientInfo'])
    story.append(details_para)
    story.append(Spacer(1, 0.3*inch))
    
    # 4. SCOPE OF WORK SECTION
    story.append(Paragraph("SCOPE OF WORK", styles['SectionHeader']))
    story.append(Spacer(1, 0.15*inch))
    
    # Enhanced table with better styling
    table_header = [
        Paragraph('S/N', styles['TableHeader']),
        Paragraph('DESCRIPTION', styles['TableHeader']),
        Paragraph('QTY', styles['TableHeader']),
        Paragraph('UNIT', styles['TableHeader']),
        Paragraph('UNIT PRICE', styles['TableHeader']),
        Paragraph('TOTAL', styles['TableHeader'])
    ]
    
    table_data = [table_header]
    
    # Add items with alternating row colors
    for i, item in enumerate(quotation.items.all(), 1):
        row_data = [
            Paragraph(str(i), styles['TableCell']),
            Paragraph(item.description or '', styles['TableCell']),
            Paragraph(f"{item.quantity:,.2f}", styles['TableCellRight']),
            Paragraph(item.unit or '', styles['TableCell']),
            Paragraph(f"AED {item.unit_price:,.2f}", styles['TableCellRight']),
            Paragraph(f"AED {item.total_amount:,.2f}", styles['TableCellBoldRight']),
        ]
        table_data.append(row_data)
    
    # MODIFIED: Items table columns readjusted to sum up to content_width (7.0 inches)
    items_table = Table(
        table_data, 
        colWidths=[0.4*inch, 3.2*inch, 0.6*inch, 0.6*inch, 1.0*inch, 1.2*inch],
        repeatRows=1  # Repeat header on new pages
    )
    
    # Apply sophisticated table styling
    table_style = [
        # Header styling
        ('BACKGROUND', (0,0), (-1,0), header_bg),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        
        # Grid and borders
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('BOX', (0,0), (-1,-1), 1.5, primary_color),
        
        # Cell padding
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        
        # Alignment
        ('ALIGN', (0,1), (0,-1), 'CENTER'),
        ('ALIGN', (2,1), (2,-1), 'RIGHT'),
        ('ALIGN', (4,1), (5,-1), 'RIGHT'),
        
        # Row height
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_gray]),
    ]
    
    items_table.setStyle(TableStyle(table_style))
    story.append(items_table)
    story.append(Spacer(1, 0.3*inch))
    
    # 5. FINANCIAL SUMMARY SECTION
    # MODIFIED: Line separator now uses full content_width
    story.append(LineSeparator(content_width, 1, border_color))
    story.append(Spacer(1, 0.2*inch))
    
    # Calculate values
    subtotal_val = f"AED {quotation.subtotal:,.2f}"
    tax_val = f"AED {quotation.tax_amount:,.2f}"
    grand_total_val = f"AED {quotation.grand_total:,.2f}"
    
    # Create summary table with enhanced styling
    summary_data = [
        [Paragraph('Subtotal:', styles['TotalLabel']), 
         Paragraph(subtotal_val, styles['TotalValue'])],
        
        [Paragraph(f'VAT ({quotation.tax_percentage}%):', styles['TotalLabel']), 
         Paragraph(tax_val, styles['TotalValue'])],
         
        [Spacer(1, 0.1*inch), Spacer(1, 0.1*inch)],
        
        [Paragraph('<b>GRAND TOTAL:</b>', styles['GrandTotal']), 
         Paragraph(f'<b>{grand_total_val}</b>', styles['GrandTotal'])],
    ]
    
    summary_table = Table(summary_data, colWidths=[1.8*inch, 1.5*inch])
    summary_table.hAlign = 'RIGHT' # Keep summary details aligned to the right
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        
        # Grand total styling
        ('BACKGROUND', (0,3), (-1,3), light_gray),
        ('BOX', (0,3), (-1,3), 1.5, accent_color),
        ('LEFTPADDING', (0,3), (-1,3), 12),
        ('RIGHTPADDING', (0,3), (-1,3), 12),
        ('TOPPADDING', (0,3), (-1,3), 10),
        ('BOTTOMPADDING', (0,3), (-1,3), 10),
        
        # Line above grand total
        ('LINEABOVE', (0,3), (-1,3), 2, primary_color),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.5*inch))
    
    # 6. TERMS AND CONDITIONS
    story.append(Paragraph("TERMS & CONDITIONS", styles['SectionHeader']))
    story.append(Spacer(1, 0.1*inch))
    
    terms_text = """
    • This quotation is valid for 30 days from the date of issue.<br/>
    • 50% advance payment required upon confirmation of order.<br/>
    • Balance payment due upon completion of work.<br/>
    • All prices are in UAE Dirhams (AED) and include 5% VAT.<br/>
    • Project timeline will be confirmed upon receipt of advance payment.<br/>
    • Any changes to the scope of work may result in price adjustments.<br/>
    • Materials and specifications are subject to availability.
    """
    
    terms_para = Paragraph(terms_text, styles['TableCell'])
    # MODIFIED: Terms box now uses full content_width
    terms_box = Table([[terms_para]], colWidths=[content_width])
    terms_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), light_gray),
        ('BOX', (0,0), (0,0), 1, border_color),
        ('LEFTPADDING', (0,0), (0,0), 15),
        ('RIGHTPADDING', (0,0), (0,0), 15),
        ('TOPPADDING', (0,0), (0,0), 12),
        ('BOTTOMPADDING', (0,0), (0,0), 12),
    ]))
    
    story.append(KeepTogether(terms_box))
    story.append(Spacer(1, 0.3*inch))
    
    # 7. SIGNATURE SECTION
    # MODIFIED: Line separator now uses full content_width
    story.append(LineSeparator(content_width, 1, border_color))
    story.append(Spacer(1, 0.3*inch))
    
    sig_data = [
        [Paragraph('For CURVACRAFT:', styles['TotalLabel']), 
         Paragraph('Client Acceptance:', styles['TotalLabel'])],
        [Spacer(1, 0.5*inch), Spacer(1, 0.5*inch)],
        ['_' * 30, '_' * 30],
        [Paragraph('Authorized Signature', styles['ContactInfo']), 
         Paragraph('Signature & Date', styles['ContactInfo'])],
    ]
    
    # MODIFIED: Signature table now uses full content_width
    sig_table = Table(sig_data, colWidths=[content_width / 2, content_width / 2])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    story.append(sig_table)
    
    # 8. THANK YOU NOTE
    story.append(Spacer(1, 0.4*inch))
    thank_you = f"""
    <para align='center'>
    <font color='#{accent_color.hexval()[2:]}' size='12'><b>Thank you for your business!</b></font><br/>
    <font color='#{secondary_color.hexval()[2:]}' size='9'>
    We look forward to working with you on this project.<br/>
    For any queries, please contact us at info@curvacraft.com
    </font>
    </para>
    """
    story.append(Paragraph(thank_you, styles['BodyText']))
    
    # --- BUILD THE PDF ---
    doc.build(story, canvasmaker=NumberedCanvas)
    
    # --- RETURN THE RESPONSE ---
    buf.seek(0)
    filename = f"Quotation_{quotation.quotation_number}_{quotation.enquiry.customer.name.replace(' ', '_')}.pdf"
    return FileResponse(buf, as_attachment=True, filename=filename)

