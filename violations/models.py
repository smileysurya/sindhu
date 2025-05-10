from django.db import models

class ViolationVideo(models.Model):
    video = models.FileField(upload_to='videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class ViolationReport(models.Model):
    video = models.ForeignKey(ViolationVideo, on_delete=models.CASCADE)
    pdf_report = models.FileField(upload_to='reports/')
    created_at = models.DateTimeField(auto_now_add=True)

class Violation(models.Model):  # THIS MUST EXIST
    VIOLATION_TYPES = [
        ('TR', 'Triple Riding'),
        ('RL', 'Red Light Jump'),
        ('SP', 'Speeding')
    ]
    report = models.ForeignKey(ViolationReport, on_delete=models.CASCADE)
    type = models.CharField(max_length=2, choices=VIOLATION_TYPES)
    image = models.ImageField(upload_to='violations/')
    detected_at = models.DateTimeField(auto_now_add=True)