import cv2
import numpy as np
import argparse
from miyabi_core import Section6Vision
from alerts import MiyabiAlertSystem
from view import MiyabiDashboard 
import webbrowser
from plyer import notification
import threading

class MiyabiSurveillanceHUD:
    def __init__(self, target_name="miyabi"):
        self.core = Section6Vision()
        self.alert_system = MiyabiAlertSystem()
        self.dashboard = MiyabiDashboard()
        self.target_name = target_name
        self.frame_count = 0
        
        # --- THE ODD FACTOR PAYLOADS ---
        self.browser_hijacked = False 
        self.detection_start_frame = 0
        
    def draw_3d_bounding_box(self, frame, x, y, w, h, confidence):
        """Draw a 3D vector bounding box with DYNAMIC DEPTH"""
        # FIX: Make the depth scale with confidence again! 
        # (Higher confidence = more 'Ethereal mass' = deeper box)
        depth_offset = int(25 * (confidence / 100)) 
        
        # Add that 'Odd Factor' Jitter back in too!
        jitter_x = int(np.sin(self.frame_count * 0.5) * 2)
        x += jitter_x
        
        color = (0, int(255 * confidence / 100), 255)
        
        # Front face
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        # Back face (Now dynamically offset!)
        cv2.rectangle(frame, (x + depth_offset, y - depth_offset), 
                     (x + w + depth_offset, y + h - depth_offset), color, 1)
        # Connecting lines
        for pt in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
            cv2.line(frame, pt, (pt[0] + depth_offset, pt[1] - depth_offset), color, 1)
            
        cv2.putText(frame, f"AURA: {confidence:.1f}%", (x, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return frame
    
    def process_frame(self, frame):
        self.frame_count += 1
        
        # 1. Extract Core Vision Data (The Brain)
        x, y, w, h, confidence = self.core.detect_miyabi_by_red_eyes(frame)
        aura_map = self.core.fft_aura_analysis(frame)
        
        # 2. Get Raw Edges for the Blueprint Panel (The Aesthetic)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # 3. Draw your custom 3D Box on the primary frame
        if x is not None:
            self.draw_3d_bounding_box(frame, x, y, w, h, confidence)
            
        
        # 4. Handle Alerts, Logging, and ACTIVE SABOTAGE!
        if confidence >= 80.0:
            # 1. The Initial Strike (Only happens on the first frame of lock-on!)
            if not self.alert_system.siren_triggered:
                self.alert_system.trigger_siren()
                self.dashboard.add_log_entry("TARGET LOCKED", confidence)
                self.detection_start_frame = self.frame_count # START THE CLOCK!
                

            # 2. The Countdown (Checks every frame until the timer hits 60!)
            if not self.browser_hijacked and self.detection_start_frame > 0 and (self.frame_count - self.detection_start_frame > 75):
                webbrowser.open("https://c.tenor.com/aFbvUkn8djMAAAAd/tenor.gif") 
                self.browser_hijacked = True
                self.dashboard.add_log_entry("CRITICAL SYSTEM FAILURE: BROWSER HIJACKED", None)
                
                # --- THE THREADED NOTIFICATION ---
                # We put it in a function and run it in the background so it doesn't freeze the camera!
                def pop_notification():
                    notification.notify(
                        title="MIYABI-OS: VOID WARNING",
                        message=f"Miyabi detected at {confidence:.1f}% aptitude.",
                        app_name="Miyabi-OS",
                        timeout=5
                    )
                threading.Thread(target=pop_notification, daemon=True).start()
                
        elif confidence < 40.0:
            # 3. The Reset Protocol (Clears everything when the target is lost)
            if self.alert_system.siren_triggered:
                self.dashboard.add_log_entry("Target lost. Resetting alarms.", confidence)
            self.alert_system.siren_triggered = False
            self.browser_hijacked = False
            self.detection_start_frame = 0 

        # 5. Delegate all rendering to view.py! 
        # No more manual array mashing here!
        dashboard_frame = self.dashboard.render(
            primary_frame=frame, 
            heatmap_frame=aura_map, 
            edge_frame=edges, 
            confidence=confidence
        )
        
        return dashboard_frame, confidence

def main():
    parser = argparse.ArgumentParser(description="Miyabi-OS Surveillance Suite")
    parser.add_argument("--target", default="miyabi", help="Target asset name")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    args = parser.parse_args()
    
    hud = MiyabiSurveillanceHUD(target_name=args.target)
    cap = cv2.VideoCapture(args.camera)
    
    # --- STEP 1: INITIALIZE THE FULLSCREEN WINDOW ---
    window_name = f"Miyabi-OS Tactical Dashboard | Target: {args.target}"
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # --- DETECT MONITOR RESOLUTION ---
    # We use a dummy window property to get the actual pixel width of your screen!
    screen_w = int(cv2.getWindowImageRect(window_name)[2])
    screen_h = int(cv2.getWindowImageRect(window_name)[3])
    
    print(f"[SYSTEM] Ultrawide detected: {screen_w}x{screen_h}. Scaling HUD...")

    while True:
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0:
            continue
        
        processed_frame, confidence = hud.process_frame(frame)

        # --- THE ULTRAWIDE ASPECT RATIO SHIELD ---
        h, w = processed_frame.shape[:2]
        aspect_ratio = w / h
        
        # Calculate the new width based on the monitor's height to keep it proportional
        new_w = int(screen_h * aspect_ratio)
        resized_hud = cv2.resize(processed_frame, (new_w, screen_h), interpolation=cv2.INTER_LINEAR)
        
        # Create a black canvas the size of your ENTIRE ultrawide monitor
        full_canvas = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)
        
        # Center the HUD on the canvas
        x_offset = (screen_w - new_w) // 2
        full_canvas[:, x_offset:x_offset + new_w] = resized_hud
        
        cv2.imshow(window_name, full_canvas)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()