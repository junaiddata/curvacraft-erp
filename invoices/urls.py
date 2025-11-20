# invoices/urls.py
from django.urls import path
from . import views

app_name = 'invoices'
urlpatterns = [
    path('create/for-project/<int:project_pk>/', views.invoice_create_edit, name='invoice_create'),
    path('<int:pk>/edit/', views.invoice_create_edit, name='invoice_edit'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/void/', views.invoice_void, name='invoice_void'),
    path('<int:pk>/pdf/', views.invoice_pdf_view, name='invoice_pdf'),
]