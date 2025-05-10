from django.shortcuts import render, get_object_or_404
from django.core.files.storage import FileSystemStorage
from fpdf import FPDF
import cv2
from ultralytics import YOLO
import os
import numpy as np
from django.conf import settings
from .models import ViolationReport, ViolationVideo, Violation  # Added missing Violation model import

def count_riders(frame: np.ndarray, bike_box) -> int:
    """
    Counts riders on a bike using YOLO detection
    """
    model = YOLO("yolov8n.pt")
    x1, y1, x2, y2 = map(int, bike_box.xyxy[0].tolist())
    
    # Expand detection area
    padding = int(0.2 * (x2 - x1))
    x1, y1 = max(0, x1 - padding), max(0, y1 - padding)
    x2, y2 = min(frame.shape[1], x2 + padding), min(frame.shape[0], y2 + padding)
    
    # Detect people in bike area
    bike_area = frame[y1:y2, x1:x2]
    results = model(bike_area, classes=[0])  # Class 0 = person
    
    return len(results[0].boxes)

def process_video(video_path):  # Added missing function definition
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(video_path)
    violations = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        results = model(frame, classes=[1, 2, 3])  # 1=bike, 2=car, 3=motorcycle
        for box in results[0].boxes:
            if box.cls == 1 and count_riders(frame, box) >= 3:
                violations.append(frame.copy())
    
    cap.release()  # Important: release video capture
    return violations[:3]

def generate_pdf(violations, fs):
    # Create reports directory if it doesn't exist
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Create violations directory if it doesn't exist
    violations_dir = os.path.join(settings.MEDIA_ROOT, 'violations')
    os.makedirs(violations_dir, exist_ok=True)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Traffic Violation Report", ln=True, align='C')
    
    for i, frame in enumerate(violations):
        img_path = os.path.join('violations', f'violation_{i}.jpg')
        full_img_path = fs.path(img_path)
        cv2.imwrite(full_img_path, frame)
        pdf.image(full_img_path, x=10, y=pdf.get_y(), w=100)
        pdf.ln(85)
    
    report_path = os.path.join('reports', f'report_{len(violations)}.pdf')
    full_report_path = fs.path(report_path)
    pdf.output(full_report_path)
    return report_path
def upload_video(request):
    if request.method == 'POST' and request.FILES['video']:
        fs = FileSystemStorage()
        
        # Save video
        video = request.FILES['video']
        video_path = fs.save(f'videos/{video.name}', video)
        video_obj = ViolationVideo.objects.create(video=video_path)
        
        # Process violations
        violations = process_video(fs.path(video_path))  # Now properly defined
        
        # Generate and save report
        report_path = generate_pdf(violations, fs)
        report = ViolationReport.objects.create(
            video=video_obj,
            pdf_report=report_path
        )
        
        # Create violation records
        for i, frame in enumerate(violations):
            img_path = f'violations/violation_{report.id}_{i}.jpg'
            cv2.imwrite(fs.path(img_path), frame)  # Fixed: added fs.path()
            Violation.objects.create(
                report=report,
                type='TR',  # Triple riding
                image=img_path  # Fixed: use relative path
            )
        
        return render(request,'violations/download.html', {
            'report_url': fs.url(report_path),
            'report_id': report.id
        })
    
    return render(request, 'violations/upload.html',{})

def view_report(request, report_id):
    report = get_object_or_404(ViolationReport, pk=report_id)
    return render(request, 'violations/report_detail.html', {
        'report': report,
        'violations': report.violation_set.all()  # Using default related_name
    })