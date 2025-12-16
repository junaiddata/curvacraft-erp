from django.urls import path
from . import views

app_name = 'enquiries'

urlpatterns = [
    path('', views.enquiry_list, name='enquiry_list'),
    path('new/', views.enquiry_create, name='enquiry_create'),
    path('<int:pk>/', views.enquiry_detail, name='enquiry_detail'),
    path('<int:pk>/edit/', views.enquiry_edit, name='enquiry_edit'),
    path('<int:pk>/delete/', views.enquiry_delete, name='enquiry_delete'),

        # --- ADD THESE NEW CUSTOMER URLs ---
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
]