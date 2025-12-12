# reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'
urlpatterns = [
    path('project/<int:project_pk>/', views.dpr_list, name='dpr_list'),
    path('project/<int:project_pk>/new/', views.dpr_create_edit, name='dpr_create'),
    path('<int:pk>/edit/', views.dpr_create_edit, name='dpr_edit'),
    path('<int:pk>/pdf/', views.dpr_pdf_view, name='dpr_pdf'),

    path('ajax/check-dpr-date/', views.ajax_check_dpr_date, name='ajax_check_dpr_date'),
]