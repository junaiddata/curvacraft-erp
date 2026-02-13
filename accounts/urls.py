# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('', views.accounts_dashboard, name='dashboard'),
    path('invoice/<int:invoice_pk>/add-payment/', views.add_payment, name='add_payment'),
    path('payment/<int:pk>/delete/', views.delete_payment, name='delete_payment'),
    path('invoice/<int:invoice_pk>/add-credit-note/', views.add_credit_note, name='add_credit_note'),

    path('export/project-summary/', views.export_project_summary_csv, name='export_project_summary'),
]