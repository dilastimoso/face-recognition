import os
import pickle
import csv
from datetime import datetime

class DataManager:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.data_file = "face_data.pkl"
        self.attendance_file = "attendance.csv"
        self.students_file = "students.csv"
        self.marked_attendance = set()
        
    def load_data(self):
        """Load face data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data['encodings']
                    self.known_face_names = data['names']
                    self.known_face_ids = [''] * len(self.known_face_names)
            except:
                self.known_face_encodings = []
                self.known_face_names = []
                self.known_face_ids = []

    def save_data(self):
        """Save face data to file"""
        try:
            with open(self.data_file, 'wb') as f:
                pickle.dump({'encodings': self.known_face_encodings, 'names': self.known_face_names}, f)
        except:
            pass

    def load_students(self):
        """Load student records"""
        if os.path.exists(self.students_file):
            try:
                with open(self.students_file, 'r') as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader:
                        if len(row) >= 3:
                            name, student_id, course = row
                            if name in self.known_face_names:
                                index = self.known_face_names.index(name)
                                if len(self.known_face_ids) <= index:
                                    self.known_face_ids.extend([''] * (index + 1 - len(self.known_face_ids)))
                                self.known_face_ids[index] = student_id
            except:
                pass

    def save_student(self, name, student_id, course):
        """Save student record"""
        try:
            file_exists = os.path.isfile(self.students_file)
            with open(self.students_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Name", "Student ID", "Course", "Registration Date"])
                writer.writerow([name, student_id, course, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except:
            pass

    def mark_attendance(self, name, attendance_queue):
        """Add attendance to queue"""
        if name not in self.marked_attendance and name != "Unknown":
            attendance_queue.put(name)

    def get_student_course(self, name):
        """Get course from student file"""
        if os.path.exists(self.students_file):
            try:
                with open(self.students_file, 'r') as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader:
                        if len(row) >= 3 and row[0] == name:
                            return row[2]
            except:
                pass
        return None

    def add_face(self, name, face_encoding):
        """Add new face to database"""
        self.known_face_encodings.append(face_encoding)
        self.known_face_names.append(name)
        self.known_face_ids.append('')
        self.save_data()

    def update_student_id(self, name, student_id):
        """Update student ID for a face"""
        index = self.known_face_names.index(name)
        self.known_face_ids[index] = student_id
