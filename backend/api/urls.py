from django.urls import path
from .views import HealthCheckView, PDFUploadView, AskView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health_check"),
    path("upload/", PDFUploadView.as_view(), name="pdf_upload"),
    path("ask/", AskView.as_view(), name="ask"),
]
