# projects/urls.py

from django.urls import path
from . import views
app_name = 'projects'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),


    path('project/<int:pk>/weekly/', views.project_weekly_reports, name='project_weekly_reports'),

    path('create/from-quotation/<int:quotation_pk>/', views.create_project_from_quotation, name='create_project'),
    # The URL to edit an existing project
    path('project/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('project/<int:pk>/daily/', views.project_daily_tasks, name='project_daily_tasks'),
    path('ajax/get-scos/', views.get_scos_as_html, name='ajax_get_scos'),
    path('project/<int:pk>/tracking/', views.project_tracking_detail, name='project_tracking_detail'),
    # This is the NEW URL for the form/edit page
    path('project/<int:pk>/tracking/edit/', views.project_tracking_edit, name='project_tracking_edit'),
    path('project/<int:pk>/tracking/pdf/', views.project_tracking_pdf, name='project_tracking_pdf'),

    path('create-direct/', views.project_create_direct, name='project_create_direct'),
    path('project/<int:pk>/import-fitout/', views.import_fitout_items, name='import_fitout_items'),

    path('project/<int:pk>/delete/', views.project_delete, name='project_delete'),


]