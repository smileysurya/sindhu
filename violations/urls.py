from django.urls import path
from . import views

app_name = 'violations'

urlpatterns = [
    path('upload/', views.upload_video, name='upload_video'),
    path('reports/<int:report_id>/', views.view_report, name='view_report'),  # Fixed syntax
]