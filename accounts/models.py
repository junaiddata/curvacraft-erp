# accounts/models.py

from django.db import models
from django.utils import timezone
from invoices.models import Invoice

class Payment(models.Model):
    """Represents a single payment made against an invoice."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=50, blank=True, help_text="e.g., Bank Transfer, Cheque, Cash")
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_paid']

    def __str__(self):
        return f"Payment of {self.amount} for {self.invoice.invoice_number}"

class CreditNote(models.Model):
    """Represents a credit issued against an invoice."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='credit_notes')
    credit_note_number = models.CharField(max_length=50, unique=True, blank=True)
    date_issued = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Automatic Credit Note Number Generation (e.g., CN-YYYYNNN)
        if not self.credit_note_number:
            current_year = timezone.now().year
            prefix = f'CN-{current_year}'
            last_note = CreditNote.objects.filter(credit_note_number__startswith=prefix).order_by('credit_note_number').last()
            if last_note:
                last_seq = int(last_note.credit_note_number[-3:])
                new_seq = last_seq + 1
            else:
                new_seq = 1
            self.credit_note_number = f'{prefix}{new_seq:03d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.credit_note_number