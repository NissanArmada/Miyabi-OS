import winsound
import os

class MiyabiAlertSystem:
    def __init__(self):
        self.siren_triggered = False
    
    def trigger_siren(self):
        """Play Miyabi-Siren audio alert"""
        try:
            # Using your raw string fix!
            siren_path = r"C:\Users\ethan\Miyabi-OS\miyabi_siren.wav"
            if os.path.exists(siren_path):
                winsound.PlaySound(siren_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                self._generate_alert_tone()
            self.siren_triggered = True
        except Exception as e:
            print(f"[ALERT] Siren activation failed: {e}")
    
    def _generate_alert_tone(self):
        """Generate synthetic alert tone using system beep"""
        winsound.Beep(800, 500)