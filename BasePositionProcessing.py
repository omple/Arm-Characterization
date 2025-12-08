import cv2
import numpy as np


class GreenTrackerCalibration:
    """Calibration parameters for pixel-to-meter conversion."""
    
    # Camera calibration values (adjust based on your camera and setup)
    FOCAL_LENGTH_PIXELS = 800  # Focal length in pixels (from camera calibration)
    KNOWN_DISTANCE_METERS = 1.0  # Known distance to object (meters)
    KNOWN_SIZE_PIXELS = 50  # Known object size in pixels at reference distance
    
    # Alternatively, use direct pixel-to-meter ratio if measured experimentally
    PIXELS_PER_METER_X = 500  # pixels per meter in X direction
    PIXELS_PER_METER_Y = 500  # pixels per meter in Y direction
    
    # Reference point (image center or actual origin in meters)
    REFERENCE_X_PIXELS = 320  # X pixel coordinate of reference point
    REFERENCE_Y_PIXELS = 240  # Y pixel coordinate of reference point
    REFERENCE_X_METERS = 0.0  # X position in meters at reference
    REFERENCE_Y_METERS = 0.0  # Y position in meters at reference


class GreenObjectTracker:
    """Tracks green colored objects in camera feed and converts positions to meters."""
    
    def __init__(self, camera_id=0):
        """Initialize the tracker with camera parameters."""
        self.camera_id = camera_id
        self.cap = None
        self.is_open = False
        self.calibration = GreenTrackerCalibration()
        
        # Green color range in HSV (for better robustness)
        # H: 35-85 (green hues)
        # S: 100-255 (saturation)
        # V: 100-255 (brightness)
        self.lower_green = np.array([35, 100, 100])
        self.upper_green = np.array([85, 255, 255])
    
    def start(self):
        """Start the camera stream."""
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.camera_id}")
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.is_open = True
        print(f"Camera {self.camera_id} started successfully")
        return True
    
    def detect_green_objects(self, frame):
        """
        Detect green colored objects in frame.
        
        Args:
            frame: Input image frame
            
        Returns:
            tuple: (mask, contours) where mask is binary image and contours are object boundaries
        """
        # Convert BGR to HSV for better color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create mask for green color
        mask = cv2.inRange(hsv, self.lower_green, self.upper_green)
        
        # Apply morphological operations to clean up mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        return mask, contours
    
    def get_object_position(self, contour):
        """
        Calculate position of object from contour.
        
        Args:
            contour: Contour of detected object
            
        Returns:
            tuple: (x_pixels, y_pixels, area) or None if contour too small
        """
        area = cv2.contourArea(contour)
        
        # Minimum area threshold to avoid noise
        if area < 50:
            return None
        
        # Get centroid
        M = cv2.moments(contour)
        if M["m00"] == 0:
            return None
        
        x = int(M["m10"] / M["m00"])
        y = int(M["m01"] / M["m00"])
        
        return x, y, area
    
    def pixels_to_meters(self, x_pixels, y_pixels):
        """
        Convert pixel coordinates to meter coordinates.
        
        Args:
            x_pixels: X position in pixels
            y_pixels: Y position in pixels
            
        Returns:
            tuple: (x_meters, y_meters)
        """
        # Convert to meters using calibration reference point
        x_meters = (x_pixels - self.calibration.REFERENCE_X_PIXELS) / self.calibration.PIXELS_PER_METER_X
        y_meters = (y_pixels - self.calibration.REFERENCE_Y_PIXELS) / self.calibration.PIXELS_PER_METER_Y
        
        # Apply reference offset
        x_meters += self.calibration.REFERENCE_X_METERS
        y_meters += self.calibration.REFERENCE_Y_METERS
        
        return x_meters, y_meters
    
    def track(self, display=True):
        """
        Continuously track green objects and output positions.
        Press 'q' to quit.
        
        Args:
            display (bool): Whether to display frames with tracking visualization
        """
        if not self.is_open:
            print("Error: Camera stream not started")
            return
        
        print("\nTracking green objects...")
        print("Press 'q' to quit\n")
        print(f"{'Frame':<8} {'X (px)':<10} {'Y (px)':<10} {'X (m)':<12} {'Y (m)':<12} {'Area':<8}")
        print("-" * 70)
        
        frame_count = 0
        
        try:
            while True:
                ret, frame = self.cap.read()
                
                if not ret:
                    print("Error: Failed to read frame")
                    break
                
                frame_count += 1
                
                # Detect green objects
                mask, contours = self.detect_green_objects(frame)
                
                # Find largest green object
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    pos_data = self.get_object_position(largest_contour)
                    
                    if pos_data:
                        x_px, y_px, area = pos_data
                        x_m, y_m = self.pixels_to_meters(x_px, y_px)
                        
                        # Print tracking data
                        print(f"{frame_count:<8} {x_px:<10} {y_px:<10} {x_m:<12.4f} {y_m:<12.4f} {area:<8.0f}")
                        
                        if display:
                            # Draw circle at detected position
                            cv2.circle(frame, (x_px, y_px), 8, (0, 255, 255), -1)
                            cv2.circle(frame, (x_px, y_px), 10, (0, 255, 255), 2)
                            
                            # Draw contour
                            cv2.drawContours(frame, [largest_contour], 0, (0, 255, 0), 2)
                            
                            # Display text with position
                            text = f"X: {x_m:.3f}m Y: {y_m:.3f}m"
                            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                                       0.7, (0, 255, 0), 2)
                
                if display:
                    # Draw reference point
                    cv2.circle(frame, (self.calibration.REFERENCE_X_PIXELS, 
                                      self.calibration.REFERENCE_Y_PIXELS), 5, (255, 0, 0), -1)
                    
                    cv2.imshow("Green Object Tracker", frame)
                    
                    # Press 'q' to quit
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        
        except KeyboardInterrupt:
            print("\n\nTracking interrupted by user")
        
        finally:
            self.stop()
    
    def stop(self):
        """Stop the camera stream and release resources."""
        if self.is_open and self.cap is not None:
            self.cap.release()
            cv2.destroyAllWindows()
            self.is_open = False
            print(f"Camera {self.camera_id} stopped")


# Example usage
if __name__ == "__main__":
    tracker = GreenObjectTracker(camera_id=0)
    
    if tracker.start():
        tracker.track(display=True)

