# users/urls.py

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # URL for our popup
    path('sco/add/', views.sco_add_popup, name='sco_add_popup'),


    # --- ADD THESE TWO NEW URLS ---
    # The page that lists all SCOs for management
    path('manage-scos/', views.manage_scos_list, name='manage_scos'),
    # The URL that will handle the toggle action
    path('sco/<int:user_pk>/toggle-active/', views.toggle_sco_status, name='toggle_sco_status'),
]