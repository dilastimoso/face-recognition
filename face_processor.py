import cv2
import face_recognition
import numpy as np

class FaceProcessor:
    def __init__(self, data_manager, attendance_queue):
        self.data_manager = data_manager
        self.attendance_queue = attendance_queue

    def process_frame(self, frame):
        """Process frame for face recognition"""
        if frame is None:
            return frame
        
        processed_frame = frame.copy()
        
        try:
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            # Process each face
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                if self.data_manager.known_face_encodings:
                    matches = face_recognition.compare_faces(self.data_manager.known_face_encodings, face_encoding)
                    name = "Unknown"
                    
                    if True in matches:
                        face_distances = face_recognition.face_distance(self.data_manager.known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = self.data_manager.known_face_names[best_match_index]
                            if name not in self.data_manager.marked_attendance:
                                self.data_manager.mark_attendance(name, self.attendance_queue)
                    
                    # Scale back face locations
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4
                    
                    # Draw rectangle and name
                    cv2.rectangle(processed_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.rectangle(processed_frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                    cv2.putText(processed_frame, name, (left + 6, bottom - 6), 
                              cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
        except Exception as e:
            print(f"Face recognition error: {e}")
        
        return processed_frame

    def register_face_from_frame(self, frame, name):
        """Register a new face from frame"""
        if frame is None:
            return False, "No frame available"
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if len(face_locations) == 1:
            face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
            return True, face_encoding
        elif len(face_locations) == 0:
            return False, "No face detected"
        else:
            return False, "Multiple faces detected"
