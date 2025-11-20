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
]