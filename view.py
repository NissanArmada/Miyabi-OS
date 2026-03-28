import cv2
import numpy as np
from datetime import datetime
from collections import deque

class MiyabiDashboard:
    def __init__(self, primary_width=1280, primary_height=720, log_capacity=15):
        self.primary_width = primary_width
        self.primary_height = primary_height
        self.panel_small_width = 320
        self.panel_small_height = 240
        self.log_capacity = log_capacity
        self.system_log = deque(maxlen=log_capacity)
        
        # Dashboard dimensions
        self.dashboard_width = primary_width + self.panel_small_width + 40
        self.dashboard_height = primary_height + 20
        
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_color = (0, 255, 0)  # Green for tactical theme
        self.font_thickness = 1
        
    def add_log_entry(self, message, confidence=None):
        """Add a timestamped message to the system log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        
        if confidence is not None:
            entry += f" ({confidence:.1f}%)"
        
        self.system_log.append(entry)
    
    def _generate_tactical_messages(self, confidence):
        """Generate contextual tactical messages based on confidence level"""
        messages = []
        
        if confidence > 80:
            messages.append("CRITICAL AURA SIGNATURE DETECTED")
            messages.append("THREAT LEVEL: MAXIMUM")
        elif confidence > 60:
            messages.append("AURA PATTERN RECOGNIZED")
            messages.append("THREAT LEVEL: HIGH")
        elif confidence > 40:
            messages.append("ANOMALY DETECTED IN VOID FIELD")
            messages.append("ANALYZING SIGNATURE...")
        else:
            messages.append("VOID STABILITY: NOMINAL")
            messages.append("SYSTEM MONITORING ACTIVE")
        
        return messages
    
    def _render_system_log(self, dashboard, confidence):
        """Render scrolling system log on the right sidebar"""
        log_x = self.primary_width + 20
        log_y = 30
        line_height = 18
        
        # Log header
        cv2.putText(dashboard, "SYSTEM LOG", (log_x, log_y - 10),
                    self.font, 0.6, (0, 255, 255), 2)
        
        # Tactical messages
        tactical_messages = self._generate_tactical_messages(confidence)
        for i, msg in enumerate(tactical_messages):
            y_pos = log_y + (i * line_height)
            cv2.putText(dashboard, msg, (log_x, y_pos),
                        self.font, self.font_scale, self.font_color, self.font_thickness)
        
        # System log entries
        start_line = 4
        for i, entry in enumerate(list(self.system_log)[-10:]):
            y_pos = log_y + ((start_line + i) * line_height)
            cv2.putText(dashboard, entry[:25], (log_x, y_pos),
                        self.font, 0.4, (100, 200, 100), 1)
    
    def render(self, primary_frame, heatmap_frame, edge_frame, confidence=0, target_box=None):
        """
        Render the tactical dashboard with all three panels.
        
        Args:
            primary_frame: Main camera feed (will be resized to primary dimensions)
            heatmap_frame: FFT Aura Heatmap
            edge_frame: Canny edge detection blueprint
            confidence: Current detection confidence (0-100)
            target_box: Optional bounding box tuple (x1, y1, x2, y2)
        
        Returns:
            dashboard_frame: Composite dashboard image
        """
        # Create base dashboard canvas
        dashboard = np.zeros((self.dashboard_height, self.dashboard_width, 3), dtype=np.uint8)
        
        # Resize and place primary frame (left panel)
        primary_resized = cv2.resize(primary_frame, (self.primary_width, self.primary_height))
        
        # Draw 3D bounding box if provided
        if target_box is not None:
            x1, y1, x2, y2 = target_box
            # Scale box to resized frame
            scale_x = self.primary_width / primary_frame.shape[1]
            scale_y = self.primary_height / primary_frame.shape[0]
            
            x1_scaled = int(x1 * scale_x)
            y1_scaled = int(y1 * scale_y)
            x2_scaled = int(x2 * scale_x)
            y2_scaled = int(y2 * scale_y)
            
            cv2.rectangle(primary_resized, (x1_scaled, y1_scaled), (x2_scaled, y2_scaled),
                         (0, 255, 255), 3)
            cv2.putText(primary_resized, f"Confidence: {confidence:.1f}%",
                       (x1_scaled, y1_scaled - 10), self.font, 0.7, (0, 255, 255), 2)
        
        dashboard[10:10+self.primary_height, 10:10+self.primary_width] = primary_resized
        
        # Resize and place heatmap (top right)
        heatmap_resized = cv2.resize(heatmap_frame, (self.panel_small_width, self.panel_small_height))
        dashboard[10:10+self.panel_small_height, 
                 self.primary_width+20:self.primary_width+20+self.panel_small_width] = heatmap_resized
        
        # Resize and place edge blueprint (bottom right)
        edge_resized = cv2.resize(edge_frame, (self.panel_small_width, self.panel_small_height))
        if len(edge_resized.shape) == 2:
            edge_resized = cv2.cvtColor(edge_resized, cv2.COLOR_GRAY2BGR)
        dashboard[10+self.panel_small_height+10:10+self.panel_small_height+10+self.panel_small_height,
                 self.primary_width+20:self.primary_width+20+self.panel_small_width] = edge_resized
        
        # Panel labels
        cv2.putText(dashboard, "PRIMARY FEED", (15, 25),
                    self.font, 0.7, (0, 255, 255), 2)
        cv2.putText(dashboard, "FFT AURA", (self.primary_width + 25, 25),
                    self.font, 0.5, (0, 255, 255), 1)
        cv2.putText(dashboard, "EDGE BLUEPRINT", (self.primary_width + 25, 260),
                    self.font, 0.5, (0, 255, 255), 1)
        
        # Render system log
        self._render_system_log(dashboard, confidence)
        
        return dashboard
    
    def display(self, dashboard_frame, window_name="MIYABI-OS Tactical Dashboard"):
        """Display the dashboard in a window"""
        cv2.imshow(window_name, dashboard_frame)
    
    def save_frame(self, dashboard_frame, filepath):
        """Save dashboard frame to disk"""
        cv2.imwrite(filepath, dashboard_frame)
