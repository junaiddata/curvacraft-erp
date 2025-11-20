# invoices/pdf_utils.py

# --- ALL IMPORTS NEEDED FOR THESE HELPERS ---
import io
import requests
from PIL import Image as PILImage, ImageOps
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import Flowable
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image

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
            pil_img = PILImage.open(io.BytesIO(response.content))
            
            if pil_img.mode != 'RGBA':
                pil_img = pil_img.convert('RGBA')
            
            r, g, b, a = pil_img.split()
            rgb_image = PILImage.merge('RGB', (r, g, b))
            inverted_rgb = ImageOps.invert(rgb_image)
            inverted_r, inverted_g, inverted_b = inverted_rgb.split()
            inverted_image = PILImage.merge('RGBA', (inverted_r, inverted_g, inverted_b, a))
            
            img_buffer = io.BytesIO()
            inverted_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return Image(img_buffer, width=2.8*inch, height=0.7*inch)
    except Exception as e:
        print(f"Header logo processing error: {e}")
    
    return None