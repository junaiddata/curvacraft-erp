# purchase_orders/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Contractor, PurchaseOrder, PurchaseOrderItem, PurchaseOrderDocument
from .forms import (
    ContractorForm, PurchaseOrderForm, PurchaseOrderItemFormSet,
    PurchaseOrderStatusForm, PurchaseOrderDocumentForm
)
from users.decorators import role_required

# PDF Generation Imports
import io
import requests
from PIL import Image as PILImage, ImageOps
from datetime import timedelta
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

# -----------------
# CONTRACTOR VIEWS
# -----------------

@role_required('admin', 'staff')
@login_required
def contractor_list(request):
    """List all contractors."""
    contractors = Contractor.objects.all().order_by('name')
    context = {'contractors': contractors}
    return render(request, 'purchase_orders/contractor_list.html', context)

@role_required('admin', 'staff')
@login_required
def contractor_detail(request, pk):
    """View contractor details with linked purchase orders."""
    contractor = get_object_or_404(Contractor, pk=pk)
    purchase_orders = contractor.purchase_orders.all().order_by('-created_at')
    context = {
        'contractor': contractor,
        'purchase_orders': purchase_orders
    }
    return render(request, 'purchase_orders/contractor_detail.html', context)

@role_required('admin', 'staff')
@login_required
def contractor_create(request):
    """Create a new contractor."""
    if request.method == 'POST':
        form = ContractorForm(request.POST)
        if form.is_valid():
            contractor = form.save()
            messages.success(request, f'Contractor "{contractor.name}" created successfully.')
            return redirect('purchase_orders:contractor_detail', pk=contractor.pk)
    else:
        form = ContractorForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'purchase_orders/contractor_form.html', context)

@role_required('admin', 'staff')
@login_required
def contractor_edit(request, pk):
    """Edit an existing contractor."""
    contractor = get_object_or_404(Contractor, pk=pk)
    
    if request.method == 'POST':
        form = ContractorForm(request.POST, instance=contractor)
        if form.is_valid():
            contractor = form.save()
            messages.success(request, f'Contractor "{contractor.name}" updated successfully.')
            return redirect('purchase_orders:contractor_detail', pk=contractor.pk)
    else:
        form = ContractorForm(instance=contractor)
    
    context = {'form': form, 'contractor': contractor, 'action': 'Edit'}
    return render(request, 'purchase_orders/contractor_form.html', context)

@role_required('admin', 'staff')
@login_required
def contractor_delete(request, pk):
    """Delete a contractor."""
    contractor = get_object_or_404(Contractor, pk=pk)
    
    if request.method == 'POST':
        name = contractor.name
        contractor.delete()
        messages.success(request, f'Contractor "{name}" deleted successfully.')
        return redirect('purchase_orders:contractor_list')
    
    context = {'contractor': contractor}
    return render(request, 'purchase_orders/contractor_confirm_delete.html', context)

# -----------------
# PURCHASE ORDER VIEWS
# -----------------

@role_required('admin', 'staff')
@login_required
def po_list(request):
    """List all purchase orders."""
    purchase_orders = PurchaseOrder.objects.all().select_related('contractor').prefetch_related('items')
    context = {'purchase_orders': purchase_orders}
    return render(request, 'purchase_orders/po_list.html', context)

@role_required('admin', 'staff')
@login_required
def po_detail(request, pk):
    """Display purchase order details, line items, documents, and status form."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    status_form = PurchaseOrderStatusForm(instance=po)
    document_form = PurchaseOrderDocumentForm()

    if request.method == 'POST':
        # Check if it's a status update
        if 'update_status' in request.POST:
            status_form = PurchaseOrderStatusForm(request.POST, instance=po)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, 'Purchase order status updated successfully.')
                return redirect('purchase_orders:po_detail', pk=po.pk)

    context = {
        'po': po,
        'status_form': status_form,
        'document_form': document_form
    }
    return render(request, 'purchase_orders/po_detail.html', context)

@role_required('admin', 'staff')
@login_required
def po_create(request):
    """Create a new purchase order."""
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        formset = PurchaseOrderItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            po = form.save(commit=False)
            po.save()
            
            formset.instance = po
            formset.save()
            
            messages.success(request, f'Purchase order {po.po_number} created successfully.')
            return redirect('purchase_orders:po_detail', pk=po.pk)
    else:
        form = PurchaseOrderForm()
        formset = PurchaseOrderItemFormSet()

    context = {
        'form': form,
        'formset': formset,
        'action': 'Create'
    }
    return render(request, 'purchase_orders/po_form.html', context)

@role_required('admin', 'staff')
@login_required
def po_edit(request, pk):
    """Edit an existing purchase order."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po)
        formset = PurchaseOrderItemFormSet(request.POST, instance=po)
        
        if form.is_valid() and formset.is_valid():
            po = form.save()
            formset.save()
            
            messages.success(request, f'Purchase order {po.po_number} updated successfully.')
            return redirect('purchase_orders:po_detail', pk=po.pk)
    else:
        form = PurchaseOrderForm(instance=po)
        formset = PurchaseOrderItemFormSet(instance=po)

    context = {
        'form': form,
        'formset': formset,
        'po': po,
        'action': 'Edit'
    }
    return render(request, 'purchase_orders/po_form.html', context)

@role_required('admin', 'staff')
@login_required
def po_delete(request, pk):
    """Delete a purchase order."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    if request.method == 'POST':
        po_number = po.po_number
        po.delete()
        messages.success(request, f'Purchase order {po_number} deleted successfully.')
        return redirect('purchase_orders:po_list')
    
    context = {'po': po}
    return render(request, 'purchase_orders/po_confirm_delete.html', context)

# -----------------
# DOCUMENT VIEWS
# -----------------

@role_required('admin', 'staff')
@login_required
def document_upload(request, pk):
    """Upload a document to a purchase order."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    if request.method == 'POST':
        form = PurchaseOrderDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.purchase_order = po
            document.save()
            messages.success(request, 'Document uploaded successfully.')
        else:
            messages.error(request, 'Error uploading document.')
    
    return redirect('purchase_orders:po_detail', pk=po.pk)

@role_required('admin', 'staff')
@login_required
@require_POST
def document_delete(request, pk):
    """Delete a document."""
    document = get_object_or_404(PurchaseOrderDocument, pk=pk)
    po_pk = document.purchase_order.pk
    document.delete()
    messages.success(request, 'Document deleted successfully.')
    return redirect('purchase_orders:po_detail', pk=po_pk)

# -----------------
# PDF GENERATION HELPERS
# -----------------

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
        
        # Footer background - COMPACT
        self.setFillColor(colors.HexColor("#FAFAFA"))
        self.rect(0, 0, letter[0], 0.8*inch, fill=1, stroke=0)
        
        # Footer line
        self.setStrokeColor(colors.HexColor("#D0D0D0"))
        self.setLineWidth(0.3)
        self.line(0.5*inch, 0.7*inch, letter[0] - 0.5*inch, 0.7*inch)
        
        # Footer text - SMALLER
        self.setFont("Helvetica", 6)
        self.setFillColor(colors.HexColor("#757575"))
        
        # Page number
        self.drawRightString(letter[0] - 0.5*inch, 0.5*inch, f"Page {self._pageNumber} of {page_count}")
        
        # Company details - left side - COMPACT
        self.drawString(0.5*inch, 0.5*inch, "CURVACRAFT DESIGN & BUILD STUDIO")
        self.drawString(0.5*inch, 0.35*inch, "reachout@curvacraft.com | www.curvacraft.com")
        self.drawString(0.5*inch, 0.2*inch, "Dubai, United Arab Emirates")
        
        self.restoreState()

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

# -----------------
# PDF VIEW
# -----------------

@login_required
@role_required('admin', 'staff')
def po_pdf_view(request, pk):
    """Generates a compact, optimized PDF purchase order"""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    buf = io.BytesIO()

    # --- SETUP DOCUMENT WITH CONSISTENT MARGINS ---
    doc = SimpleDocTemplate(
        buf, 
        pagesize=letter,
        rightMargin=0.5*inch, 
        leftMargin=0.5*inch,
        topMargin=0.6*inch, 
        bottomMargin=0.8*inch,
        title=f"Purchase Order {po.po_number}",
        author="CURVACRAFT DESIGN & BUILD STUDIO"
    )
    
    # --- DEFINE CONTENT WIDTH FOR ALIGNMENT ---
    content_width = doc.width
    # Consistent padding for all boxes
    box_padding = 8

    # --- PROFESSIONAL COLOR PALETTE ---
    primary_color = colors.HexColor("#2C3E50")      # Dark blue-gray
    accent_color = colors.HexColor("#9d9084")       # Golden accent
    secondary_color = colors.HexColor("#7F8C8D")    # Medium gray
    light_gray = colors.HexColor("#ECF0F1")         # Very light gray
    border_color = colors.HexColor("#BDC3C7")       # Border gray
    header_bg = colors.HexColor("#34495E")          # Dark header
    
    # --- ENHANCED STYLES ---
    styles = getSampleStyleSheet()
    
    # Custom styles - REDUCED SIZES FOR COMPACT LAYOUT
    styles.add(ParagraphStyle(
        name='CompanyName',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=primary_color,
        spaceAfter=4,
        alignment=TA_LEFT
    ))
    
    styles.add(ParagraphStyle(
        name='POTitle',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=accent_color,
        alignment=TA_RIGHT,
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4,
        borderColor=accent_color,
        borderWidth=1,
        borderPadding=2,
        leftIndent=0
    ))
    
    styles.add(ParagraphStyle(
        name='ContactInfo',
        fontName='Helvetica',
        fontSize=7,
        textColor=secondary_color,
        leading=9
    ))
    
    styles.add(ParagraphStyle(
        name='ContractorInfo',
        fontName='Helvetica',
        fontSize=8,
        textColor=primary_color,
        leading=10
    ))
    
    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=7,
        textColor=colors.white,
        alignment=TA_CENTER,
        leading=9,  # Fixed line height to prevent wrapping
        spaceBefore=0,
        spaceAfter=0
    ))
    
    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=7,
        textColor=primary_color,
        leading=9
    ))
    
    styles.add(ParagraphStyle(
        name='TableCellRight',
        fontName='Helvetica',
        fontSize=7,
        textColor=primary_color,
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='TableCellBoldRight',
        fontName='Helvetica-Bold',
        fontSize=7,
        textColor=primary_color,
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='TotalLabel',
        fontName='Helvetica',
        fontSize=8,
        textColor=secondary_color,
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='TotalValue',
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=primary_color,
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='GrandTotal',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=accent_color,
        alignment=TA_RIGHT
    ))

    # --- BUILD STORY ---
    story = []

    # 1. PROFESSIONAL HEADER WITH LOGO
    logo_url = "https://curvacraft.com/wp-content/uploads/2024/10/Curvacraft-logo-1024x255.webp"
    logo = process_logo(logo_url)
    
    if not logo:
        logo = Paragraph("<b>CURVACRAFT</b><br/><font size='7'>DESIGN & BUILD STUDIO</font>", styles['CompanyName'])
    
    # Header table with logo and PO info - COMPACT
    po_info = f"""
        <font size='12' color='#{accent_color.hexval()[2:]}'><b>PURCHASE ORDER</b></font><br/>
        <font size='7' color='#{secondary_color.hexval()[2:]}'>#{po.po_number}</font><br/>
        <font size='7' color='#{secondary_color.hexval()[2:]}'>{po.created_at:%d %B %Y}</font>
    """
    
    header_data = [[
        logo,
        Paragraph(po_info, styles['POTitle'])
    ]]
    
    # Header table - FULL WIDTH with consistent alignment
    header_table = Table(header_data, colWidths=[content_width - 2.0*inch, 2.0*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 0.1*inch))
    story.append(LineSeparator(content_width, 1, accent_color))
    story.append(Spacer(1, 0.15*inch))
    
    # 2. CONTRACTOR AND COMPANY INFORMATION - COMPACT
    contractor_info = f"""
        <font color='#{accent_color.hexval()[2:]}' size='8'><b>CONTRACTOR DETAILS</b></font><br/>
        <font size='8'><b>{po.contractor.name}</b></font><br/>
        """
    
    if po.contractor.contact_person:
        contractor_info += f"Contact: {po.contractor.contact_person}<br/>"
    if po.contractor.email:
        contractor_info += f"{po.contractor.email}<br/>"
    if po.contractor.phone_number:
        contractor_info += f"{po.contractor.phone_number}<br/>"
    if po.contractor.address:
        contractor_info += f"{po.contractor.address}"
    
    company_info = f"""
        <font color='#{accent_color.hexval()[2:]}' size='8'><b>FROM</b></font><br/>
        <font size='8'><b>CURVACRAFT DESIGN & BUILD STUDIO</b></font><br/>
        Studio Management Division<br/>
        reachout@curvacraft.com<br/>
        www.curvacraft.com
    """
    
    info_data = [[
        Paragraph(contractor_info, styles['ContractorInfo']),
        Paragraph(company_info, styles['ContractorInfo'])
    ]]
    
    # Info table - FULL WIDTH with CONSISTENT PADDING
    info_table = Table(info_data, colWidths=[content_width / 2, content_width / 2])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BACKGROUND', (0,0), (-1,-1), light_gray),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('LEFTPADDING', (0,0), (-1,-1), box_padding),
        ('RIGHTPADDING', (0,0), (-1,-1), box_padding),
        ('TOPPADDING', (0,0), (-1,-1), box_padding),
        ('BOTTOMPADDING', (0,0), (-1,-1), box_padding),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.2*inch))
    
    # 3. ITEMS TABLE - COMPACT
    story.append(Spacer(1, 0.1*inch))
    
    # Enhanced table with better styling - NO WRAPPING
    # Use non-breaking formatting for S/N to prevent line breaks
    table_header = [
        Paragraph('S/N', styles['TableHeader']),
        Paragraph('DESCRIPTION', styles['TableHeader']),
        Paragraph('QTY', styles['TableHeader']),
        Paragraph('UNIT', styles['TableHeader']),
        Paragraph('UNIT PRICE', styles['TableHeader']),
        Paragraph('TOTAL', styles['TableHeader'])
    ]
    
    table_data = [table_header]
    
    # Add items with alternating row colors - PROPER ALIGNMENT
    for i, item in enumerate(po.items.all(), 1):
        row_data = [
            Paragraph(str(i), styles['TableCell']),  # S/N - will be centered
            Paragraph(item.description or '', styles['TableCell']),  # Description - left aligned
            Paragraph(f"{item.quantity:,.2f}", styles['TableCellRight']),  # QTY - right aligned
            Paragraph(item.unit or '', styles['TableCell']),  # UNIT - will be centered
            Paragraph(f"AED {item.unit_price:,.2f}", styles['TableCellRight']),  # Unit Price - right aligned
            Paragraph(f"AED {item.total_amount:,.2f}", styles['TableCellBoldRight']),  # Total - right aligned
        ]
        table_data.append(row_data)
    
    # COMPACT TABLE - FULL WIDTH with PROPER ALIGNMENT
    # Calculate column widths to sum to content_width
    # Increased S/N width to prevent text wrapping
    sn_width = 0.45*inch  # Increased to prevent "S/N" from wrapping
    qty_width = 0.5*inch
    unit_width = 0.5*inch
    unit_price_width = 0.9*inch
    total_width = 1.0*inch
    desc_width = content_width - (sn_width + qty_width + unit_width + unit_price_width + total_width)
    
    items_table = Table(
        table_data, 
        colWidths=[sn_width, desc_width, qty_width, unit_width, unit_price_width, total_width],
        repeatRows=1  # Repeat header on new pages
    )
    
    # Apply compact table styling with CONSISTENT PADDING
    table_style = [
        # Header styling
        ('BACKGROUND', (0,0), (-1,0), header_bg),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 7),
        ('ALIGN', (0,0), (0,0), 'CENTER'),  # S/N centered
        ('ALIGN', (1,0), (1,0), 'LEFT'),    # Description left
        ('ALIGN', (2,0), (2,0), 'CENTER'),  # QTY centered
        ('ALIGN', (3,0), (3,0), 'CENTER'),  # UNIT centered
        ('ALIGN', (4,0), (5,0), 'RIGHT'),   # Prices right
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        
        # Grid and borders - thinner
        ('GRID', (0,0), (-1,-1), 0.3, border_color),
        ('BOX', (0,0), (-1,-1), 1, primary_color),
        
        # Cell padding - CONSISTENT
        ('LEFTPADDING', (0,0), (-1,-1), box_padding),
        ('RIGHTPADDING', (0,0), (-1,-1), box_padding),
        ('TOPPADDING', (0,0), (-1,-1), box_padding),
        ('BOTTOMPADDING', (0,0), (-1,-1), box_padding),
        
        # Alignment for data rows
        ('ALIGN', (0,1), (0,-1), 'CENTER'),  # S/N centered
        ('ALIGN', (1,1), (1,-1), 'LEFT'),    # Description left-aligned
        ('ALIGN', (2,1), (2,-1), 'RIGHT'),   # QTY right-aligned
        ('ALIGN', (3,1), (3,-1), 'CENTER'),  # UNIT centered
        ('ALIGN', (4,1), (5,-1), 'RIGHT'),   # Prices right-aligned
        
        # Row height - compact
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_gray]),
    ]
    
    items_table.setStyle(TableStyle(table_style))
    story.append(items_table)
    story.append(Spacer(1, 0.15*inch))
    
    # 5. FINANCIAL SUMMARY SECTION - COMPACT
    story.append(LineSeparator(content_width, 0.5, border_color))
    story.append(Spacer(1, 0.1*inch))
    
    # Calculate values
    subtotal_val = f"AED {po.subtotal:,.2f}"
    tax_val = f"AED {po.tax_amount:,.2f}"
    grand_total_val = f"AED {po.grand_total:,.2f}"
    
    # Create summary table - COMPACT with CONSISTENT ALIGNMENT
    summary_data = [
        [Paragraph('Subtotal:', styles['TotalLabel']), 
         Paragraph(subtotal_val, styles['TotalValue'])],
        
        [Paragraph(f'VAT ({po.tax_percentage}%):', styles['TotalLabel']), 
         Paragraph(tax_val, styles['TotalValue'])],
         
        [Spacer(1, 0.05*inch), Spacer(1, 0.05*inch)],
        
        [Paragraph('<b>GRAND TOTAL:</b>', styles['GrandTotal']), 
         Paragraph(f'<b>{grand_total_val}</b>', styles['GrandTotal'])],
    ]
    
    # Summary table aligned to RIGHT edge with consistent width
    summary_width = 2.7*inch
    summary_table = Table(summary_data, colWidths=[1.5*inch, 1.2*inch])
    summary_table.hAlign = 'RIGHT'
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        
        # Grand total styling - compact with CONSISTENT PADDING
        ('BACKGROUND', (0,3), (-1,3), light_gray),
        ('BOX', (0,3), (-1,3), 1, accent_color),
        ('LEFTPADDING', (0,3), (-1,3), box_padding),
        ('RIGHTPADDING', (0,3), (-1,3), box_padding),
        ('TOPPADDING', (0,3), (-1,3), box_padding),
        ('BOTTOMPADDING', (0,3), (-1,3), box_padding),
        
        # Consistent padding for all rows
        ('LEFTPADDING', (0,0), (-1,2), box_padding),
        ('RIGHTPADDING', (0,0), (-1,2), box_padding),
        ('TOPPADDING', (0,0), (-1,2), box_padding),
        ('BOTTOMPADDING', (0,0), (-1,2), box_padding),
        
        # Line above grand total
        ('LINEABOVE', (0,3), (-1,3), 1, primary_color),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.25*inch))
    
    # 6. TERMS AND CONDITIONS - COMPACT
    story.append(Paragraph("TERMS & CONDITIONS", styles['SectionHeader']))
    story.append(Spacer(1, 0.05*inch))
    
    terms_text = """
    • This purchase order is valid for 30 days from the date of issue.<br/>
    • 50% advance payment required upon confirmation of order.<br/>
    • Balance payment due upon completion and delivery of work.<br/>
    • All prices are in UAE Dirhams (AED) and include 5% VAT.<br/>
    • Delivery timeline will be confirmed upon receipt of advance payment.<br/>
    • Any changes to the scope of work may result in price adjustments.<br/>
    • Materials and specifications must meet quality standards as agreed.
    """
    
    terms_para = Paragraph(terms_text, styles['TableCell'])
    # Terms box - FULL WIDTH with CONSISTENT PADDING
    terms_box = Table([[terms_para]], colWidths=[content_width])
    terms_box.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('BACKGROUND', (0,0), (0,0), light_gray),
        ('BOX', (0,0), (0,0), 0.5, border_color),
        ('LEFTPADDING', (0,0), (0,0), box_padding),
        ('RIGHTPADDING', (0,0), (0,0), box_padding),
        ('TOPPADDING', (0,0), (0,0), box_padding),
        ('BOTTOMPADDING', (0,0), (0,0), box_padding),
    ]))
    
    story.append(KeepTogether(terms_box))
    story.append(Spacer(1, 0.15*inch))
    
    # 7. SIGNATURE SECTION - COMPACT
    story.append(LineSeparator(content_width, 0.5, border_color))
    story.append(Spacer(1, 0.15*inch))
    
    sig_data = [
        [Paragraph('For CURVACRAFT:', styles['TotalLabel']), 
         Paragraph('Contractor Acceptance:', styles['TotalLabel'])],
        [Spacer(1, 0.3*inch), Spacer(1, 0.3*inch)],
        ['_' * 25, '_' * 25],
        [Paragraph('Authorized Signature', styles['ContactInfo']), 
         Paragraph('Signature & Date', styles['ContactInfo'])],
    ]
    
    # Signature table - FULL WIDTH with CONSISTENT ALIGNMENT
    sig_table = Table(sig_data, colWidths=[content_width / 2, content_width / 2])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(sig_table)
    
    # 8. THANK YOU NOTE - COMPACT
    story.append(Spacer(1, 0.2*inch))
    thank_you = f"""
    <para align='center'>
    <font color='#{accent_color.hexval()[2:]}' size='9'><b>Thank you for your service!</b></font><br/>
    <font color='#{secondary_color.hexval()[2:]}' size='7'>
    We look forward to working with you on this order.<br/>
    For any queries, please contact us at reachout@curvacraft.com
    </font>
    </para>
    """
    story.append(Paragraph(thank_you, styles['BodyText']))
    
    # --- BUILD THE PDF ---
    doc.build(story, canvasmaker=NumberedCanvas)
    
    # --- RETURN THE RESPONSE ---
    buf.seek(0)
    filename = f"PO_{po.po_number}_{po.contractor.name.replace(' ', '_')}.pdf"
    return FileResponse(buf, as_attachment=True, filename=filename)
