# progress/urls.py

from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    # Example URL: /progress/detail/5/
    path('detail/<int:pk>/', views.daily_progress_detail, name='daily_progress_detail'),
    path('weekly/detail/<int:pk>/', views.weekly_progress_detail, name='weekly_progress_detail'),
]