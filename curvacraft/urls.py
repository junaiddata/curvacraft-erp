"""
URL configuration for curvacraft project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Import settings
from django.conf.urls.static import static # Import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # --- NEW URL STRUCTURE ---
    path('', include('core.urls', namespace='core')), # The new homepage
    path('projects/', include('projects.urls', namespace='projects')), # Projects now live here
    
    path('progress/', include('progress.urls', namespace='progress')),
    path('enquiries/', include('enquiries.urls', namespace='enquiries')),
    path('quotations/', include('quotations.urls', namespace='quotations')),
    path('users/', include('users.urls', namespace='users')),
    path('invoices/', include('invoices.urls', namespace='invoices')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)