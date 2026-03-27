import cv2
import numpy as np
import argparse
from miyabi_core import Section6Vision
from alerts import MiyabiAlertSystem

class MiyabiSurveillanceHUD:
    def __init__(self, target_name="miyabi"):
        self.vision_core = Section6Vision()
        self.alert_system = MiyabiAlertSystem()
        self.target_name = target_name
        self.confidence_history = []
        self.frame_count = 0
        
    def draw_3d_bounding_box(self, frame, x, y, w, h, confidence):
        """Draw a 3D vector bounding box overlay"""
        # Project 2D box to pseudo-3D
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
        """Main frame processing pipeline"""
        self.frame_count += 1
        height, width = frame.shape[:2]
        
        # Apply blueprint aesthetic
        hud_frame = self.apply_canny_blueprint(frame)
        
        # Real detection: red eye tracking
        x, y, w, h, confidence = self.vision_core.detect_miyabi_by_red_eyes(frame)
        
        # Fallback to pseudo-detection if nothing detected
        if confidence == 0:
            center_x, center_y = width // 2, height // 2
            box_size = 50
            x, y, w, h = center_x - box_size, center_y - box_size, box_size * 2, box_size * 2
            confidence = 0
        
        self.confidence_history.append(confidence)
        
        # Draw 3D bounding box
        hud_frame = self.draw_3d_bounding_box(hud_frame, x, y, w, h, confidence)
        
        # FFT aura overlay (top-right corner)
        aura_map = self.vision_core.fft_aura_analysis(frame)
        aura_resized = cv2.resize(aura_map, (200, 150))
        hud_frame[20:170, width-220:width-20] = aura_resized
        
        # HUD text overlay
        cv2.putText(hud_frame, f"CONFIDENCE: {confidence:.1f}%", (20, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(hud_frame, f"DETECTION: {'LOCKED' if confidence > 0 else 'SEARCHING'}", (20, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(hud_frame, f"FRAME: {self.frame_count}", (20, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        
        # Trigger alerts at 80% confidence
        if confidence >= 80.0:
            self.alert_system.trigger_siren()
            self.alert_system.send_alert_email(self.target_name, confidence, self.frame_count)
        
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
