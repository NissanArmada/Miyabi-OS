import smtplib
import winsound
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class MiyabiAlertSystem:
    def __init__(self, email_config=None):
        self.siren_triggered = False
        self.email_config = email_config or {
            "sender": os.getenv("MIYABI_EMAIL", "surveillance@section6.local"),
            "password": os.getenv("MIYABI_PASSWORD", ""),
            "recipient": os.getenv("MIYABI_RECIPIENT", "ops@section6.local"),
            "smtp_server": os.getenv("MIYABI_SMTP", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("MIYABI_SMTP_PORT", "587"))
        }
    
    def trigger_siren(self):
        """Play Miyabi-Siren audio alert"""
        try:
            siren_path = "assets/miyabi_siren.wav"
            if os.path.exists(siren_path):
                winsound.PlaySound(siren_path, winsound.SND_FILENAME)
            else:
                # Fallback: generate beep
                self._generate_alert_tone()
            self.siren_triggered = True
        except Exception as e:
            print(f"[ALERT] Siren activation failed: {e}")
    
    def _generate_alert_tone(self):
        """Generate synthetic alert tone using system beep"""
        frequency = 800  # Hz
        duration = 500   # milliseconds
        winsound.Beep(frequency, duration)
    
    def send_alert_email(self, target_name, confidence, frame_number):
        """Send SMTP emergency contact notification"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = MIMEMultipart()
            message["From"] = self.email_config["sender"]
            message["To"] = self.email_config["recipient"]
            message["Subject"] = f"[CRITICAL] {target_name.upper()} DETECTED | Confidence: {confidence:.1f}%"
            
            body = f"""
MIYABI-OS INCIDENT REPORT
==========================
Timestamp: {timestamp}
Target: {target_name}
Confidence Level: {confidence:.1f}%
Detection Frame: {frame_number}

Status: TARGET ACQUIRED ⚠️
Action: Automated response initiated.

This is an automated alert from Section 6 Operational Surveillance.
"""
            
            message.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(self.email_config["sender"], self.email_config["password"])
                server.send_message(message)
            
            print(f"[ALERT] Email notification sent at {timestamp}")
        except Exception as e:
            print(f"[ALERT] Email failed (non-critical): {e}")
