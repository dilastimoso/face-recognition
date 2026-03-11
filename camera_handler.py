import cv2
import time
import queue

class CameraHandler:
    def __init__(self):
        self.video_capture = None
        self.current_cam_index = 0
        self.camera_available = False
        self.frame_skip = 0
        self.current_frame = None
        
    def get_available_cameras_mac(self):
        """Get available cameras specifically for Mac"""
        available_cameras = []
        
        for i in range(2):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        available_cameras.append(i)
                    cap.release()
                time.sleep(0.1)
            except Exception as e:
                print(f"Camera {i} error: {e}")
                continue
        
        if not available_cameras:
            try:
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        available_cameras.append(0)
                    cap.release()
            except:
                pass
        
        return available_cameras if available_cameras else [0]

    def get_available_cameras(self):
        """Detect available cameras - limited to 2 for Mac"""
        available_cameras = []
        
        for i in range(2):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        available_cameras.append(i)
                    cap.release()
                time.sleep(0.1)
            except:
                pass
        
        if not available_cameras:
            available_cameras = [0]
            
        return available_cameras

    def init_camera(self, camera_index=0):
        """Initialize camera with better error handling for Mac"""
        try:
            if self.video_capture:
                self.video_capture.release()
                time.sleep(0.2)
            
            if camera_index > 1:
                camera_index = 0
            
            self.current_cam_index = camera_index
            self.video_capture = cv2.VideoCapture(camera_index)
            
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if not self.video_capture.isOpened():
                print(f"Failed to open camera {camera_index}, trying default...")
                self.video_capture = cv2.VideoCapture(0)
                self.current_cam_index = 0
                
            if self.video_capture.isOpened():
                ret, frame = self.video_capture.read()
                if not ret or frame is None:
                    print("Camera opened but cannot read frames")
                    self.camera_available = False
                else:
                    self.camera_available = True
                    self.current_frame = frame
            else:
                self.camera_available = False
                
        except Exception as e:
            print(f"Camera initialization error: {e}")
            self.video_capture = None
            self.camera_available = False

    def change_camera(self, selected_index):
        """Change camera with better error handling for Mac"""
        try:
            if self.video_capture:
                self.video_capture.release()
                time.sleep(0.2)
            
            if selected_index > 1:
                selected_index = 0
            
            self.current_cam_index = selected_index
            self.video_capture = cv2.VideoCapture(selected_index)
            
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if not self.video_capture.isOpened():
                return False, f"Camera {selected_index} is not available."
            
            ret, frame = self.video_capture.read()
            if not ret or frame is None:
                print("Camera opened but cannot read frames")
                return True, "Camera opened but cannot read frames"
            
            self.current_frame = frame
            return True, "Camera changed successfully"
                
        except Exception as e:
            return False, str(e)

    def read_frame(self):
        """Read a frame from camera"""
        if self.video_capture and self.video_capture.isOpened() and self.camera_available:
            try:
                ret, frame = self.video_capture.read()
                if ret and frame is not None:
                    self.current_frame = frame.copy()
                    return True, frame
                else:
                    return False, None
            except:
                return False, None
        return False, None

    def release_camera(self):
        """Release camera resources"""
        if self.video_capture:
            self.video_capture.release()
