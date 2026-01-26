# purchase_orders/urls.py

from django.urls import path
from . import views

app_name = 'purchase_orders'

urlpatterns = [
    # Purchase Order URLs
    path('', views.po_list, name='po_list'),
    path('create/', views.po_create, name='po_create'),
    path('<int:pk>/', views.po_detail, name='po_detail'),
    path('<int:pk>/edit/', views.po_edit, name='po_edit'),
    path('<int:pk>/delete/', views.po_delete, name='po_delete'),
    path('<int:pk>/pdf/', views.po_pdf_view, name='po_pdf'),
    
    # Document URLs
    path('<int:pk>/documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),
    
    # Contractor URLs
    path('contractors/', views.contractor_list, name='contractor_list'),
    path('contractors/create/', views.contractor_create, name='contractor_create'),
    path('contractors/<int:pk>/', views.contractor_detail, name='contractor_detail'),
    path('contractors/<int:pk>/edit/', views.contractor_edit, name='contractor_edit'),
    path('contractors/<int:pk>/delete/', views.contractor_delete, name='contractor_delete'),
]
