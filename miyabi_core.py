import cv2
import numpy as np
from scipy import signal

class Section6Vision:
    def __init__(self):
        self.fft_cache = None
    
    def calculate_laplacian_variance(self, frame):
        """Laplacian variance for focus detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        return min(100, variance / 10)
    
    def extract_eigen_miyabi(self, frame):
        """Eigenvalue analysis for 'aura' detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners = cv2.cornerHarris(gray, 2, 3, 0.04)
        aura_score = np.sum(corners) / (frame.shape[0] * frame.shape[1])
        return min(100, aura_score * 1000)
    
    def fft_aura_analysis(self, frame):
        """FFT-based frequency analysis for aura mapping"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fft = np.fft.fft2(gray)
        fft_shift = np.fft.fftshift(fft)
        magnitude_spectrum = np.log1p(np.abs(fft_shift))
        normalized = cv2.normalize(magnitude_spectrum, None, 0, 255, cv2.NORM_MINMAX)
        return np.uint8(normalized)
    
    def detect_miyabi_by_red_eyes(self, frame):
        """Detect Miyabi plushie by red eye markers"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Red color range (HSV)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = mask1 | mask2
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 50:  # Filter noise
                x, y, w, h = cv2.boundingRect(largest)
                confidence = min(100, (cv2.contourArea(largest) / 1000))
                return x, y, w, h, confidence
        
        return None, None, None, None, 0