import cv2
import numpy as np
from ultralytics import YOLO
from fpdf import FPDF
import os
from datetime import datetime

class TrafficViolationProcessor:
    def __init__(self):
        self.vehicle_model = YOLO("yolov8n.pt")
        self.temp_dir = "temp_violations"
        os.makedirs(self.temp_dir, exist_ok=True)

    def count_riders(self, frame: np.ndarray, bike_box) -> int:
        """Count riders on a bike with expanded detection area"""
        x1, y1, x2, y2 = map(int, bike_box.xyxy[0].tolist())
        padding = int(0.2 * (x2 - x1))
        
        # Expand detection area
        x1, y1 = max(0, x1 - padding), max(0, y1 - padding)
        x2, y2 = min(frame.shape[1], x2 + padding), min(frame.shape[0], y2 + padding)
        
        # Detect people in bike area
        bike_area = frame[y1:y2, x1:x2]
        results = self.vehicle_model(bike_area, classes=[0])  # Class 0 = person
        return len(results[0].boxes)

    def process_video(self, video_path: str) -> dict:
        """Process video and return violations with metadata"""
        violations = []
        cap = cv2.VideoCapture(video_path)
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                results = self.vehicle_model(frame, classes=[1, 2, 3])  # 1=bike, 2=car, 3=motorcycle
                for box in results[0].boxes:
                    if box.cls == 1 and self.count_riders(frame, box) >= 3:
                        violations.append(frame.copy())
                        
            return {
                'violations': violations[:3],  # Return first 3 violations
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'violation_count': len(violations)
            }
        finally:
            cap.release()

    def generate_pdf_report(self, violations: list) -> str:
        """Generate PDF report from violation frames"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Traffic Violation Report", ln=True, align='C')
        
        # Save temporary images and add to PDF
        img_paths = []
        for i, frame in enumerate(violations):
            img_path = os.path.join(self.temp_dir, f"violation_{i}.jpg")
            cv2.imwrite(img_path, frame)
            pdf.image(img_path, x=10, y=pdf.get_y(), w=100)
            pdf.ln(85)
            img_paths.append(img_path)
        
        report_path = os.path.join(self.temp_dir, "report.pdf")
        pdf.output(report_path)
        
        # Cleanup temporary images
        for img_path in img_paths:
            os.remove(img_path)
            
        return report_path

# Example usage:
if __name__ == "__main__":
    processor = TrafficViolationProcessor()
    results = processor.process_video("input.mp4")
    report_path = processor.generate_pdf_report(results['violations'])
    print(f"Report generated at: {report_path}")