# progress/urls.py

from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    path('review/', views.daily_progress_review_list, name='daily_progress_review_list'),
    path('detail/<int:pk>/', views.daily_progress_detail, name='daily_progress_detail'),
    path('weekly/detail/<int:pk>/', views.weekly_progress_detail, name='weekly_progress_detail'),
]