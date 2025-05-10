from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    
    path('violations/', include('violations.urls')),
    path('', RedirectView.as_view(url='violations/upload/')),  # Redirect root to upload page
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)