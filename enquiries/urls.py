from django.urls import path
from . import views

app_name = 'enquiries'

urlpatterns = [
    path('', views.enquiry_list, name='enquiry_list'),
    path('new/', views.enquiry_create, name='enquiry_create'),
    path('<int:pk>/', views.enquiry_detail, name='enquiry_detail'),
    path('<int:pk>/edit/', views.enquiry_edit, name='enquiry_edit'),
    
]