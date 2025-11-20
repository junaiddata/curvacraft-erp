# quotations/urls.py
from django.urls import path
from . import views

app_name = 'quotations'

urlpatterns = [
    # The list page
    path('', views.quotation_list, name='quotation_list'),
    # The creation page, linked from an enquiry



        # The new gateway URL
    path('manage/enquiry-<int:enquiry_pk>/type-<str:quote_type>/', views.manage_quotation, name='manage_quotation'),
    path('<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('<int:pk>/pdf/', views.quotation_pdf_view, name='quotation_pdf'),
]