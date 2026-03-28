import cv2
import numpy as np
import argparse
from miyabi_core import Section6Vision
from alerts import MiyabiAlertSystem

class MiyabiSurveillanceHUD:
    def __init__(self, target_name="miyabi"):
        # FIX 1: Unified the name to self.core!
        self.core = Section6Vision()
        self.alert_system = MiyabiAlertSystem()
        self.target_name = target_name
        self.confidence_history = []
        self.frame_count = 0
        
    def draw_3d_bounding_box(self, frame, x, y, w, h, confidence):
        """Draw a 3D vector bounding box overlay"""
        depth_offset = int(10 * (confidence / 100))
        color = (0, int(255 * confidence / 100), 255)  # Cyan to red gradient
        
        # Front face
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        # Back face (offset)
        cv2.rectangle(frame, (x + depth_offset, y - depth_offset), 
                     (x + w + depth_offset, y + h - depth_offset), color, 1)
        # Connecting lines
        for pt in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
            cv2.line(frame, pt, (pt[0] + depth_offset, pt[1] - depth_offset), color, 1)
        
        return frame
    
    def apply_canny_blueprint(self, frame):
        """Digital blueprint aesthetic using Canny edge detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        blueprint = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        blueprint[:, :, 0] = edges  # Blue channel
        blueprint[:, :, 1] = edges // 2  # Green channel
        blueprint[:, :, 2] = 0  # Red channel (minimal)
        
        return cv2.addWeighted(frame, 0.6, blueprint, 0.4, 0)
    
    def process_frame(self, frame):
        # FIX 4: Make time move forward so the Scouter fluctuates!
        self.frame_count += 1
        
        # 1. Get detection data from the core
        x, y, w, h, confidence = self.core.detect_miyabi_by_red_eyes(frame)
        aura_map = self.core.fft_aura_analysis(frame)
        
        # 2. Create the HUD base (digital blueprint)
        # FIX 2: Call self.apply_canny_blueprint, not self.core!
        hud_frame = self.apply_canny_blueprint(frame)
        height, width, _ = hud_frame.shape
        
        # 3. Paste the FFT Aura Heatmap
        aura_resized = cv2.resize(aura_map, (200, 150))
        aura_color = cv2.applyColorMap(aura_resized, cv2.COLORMAP_JET)
        hud_frame[20:170, width-220:width-20] = aura_color

        # --- SCOUTER MODE & ALERTS ---
        if confidence >= 80.0 and not self.alert_system.siren_triggered:
            self.alert_system.trigger_siren()
        elif confidence < 40.0:
            self.alert_system.siren_triggered = False
        
        color = (0, 255, 0) if confidence < 80 else (0, 0, 255)
        
        # Display the boring Confidence Percentage (Hmph!)
        cv2.putText(hud_frame, f"CONFIDENCE: {confidence:.1f}%", (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        
        status_text = "STATUS: NOMINAL"
        if confidence >= 80:
            status_text = "MIYABI SPOTTED!"
        elif confidence > 0:
            status_text = "DETECTING ANOMALY..."
        else:
            status_text = "SCANNING VOID..."
            
        cv2.putText(hud_frame, status_text, (20, 85), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # 4. Draw the 3D Vector Box if locked
        if x is not None:
            # FIX 3: Call self.draw_3d_bounding_box and pass all the right variables!
            self.draw_3d_bounding_box(hud_frame, x, y, w, h, confidence)
            
        return hud_frame, confidence

def main():
    parser = argparse.ArgumentParser(description="Miyabi-OS Surveillance Suite")
    parser.add_argument("--target", default="miyabi", help="Target asset name")
    parser.add_argument("--aura_math", default="forbidden", help="Analysis mode")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    args = parser.parse_args()
    
    hud = MiyabiSurveillanceHUD(target_name=args.target)
    cap = cv2.VideoCapture(args.camera)
    
    print("[SYSTEM] Miyabi-OS initialized. Standing by...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        processed_frame, confidence = hud.process_frame(frame)
        cv2.imshow(f"Miyabi-OS Surveillance HUD | Target: {args.target}", processed_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()