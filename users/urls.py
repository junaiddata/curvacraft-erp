# users/urls.py

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # URL for our popup
    path('sco/add/', views.sco_add_popup, name='sco_add_popup'),
]