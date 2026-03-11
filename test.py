import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import cv2
from PIL import Image, ImageTk, ImageDraw, ImageFont
import face_recognition
import numpy as np
import os
import pickle
import csv
from datetime import datetime
import threading
import platform
import queue
import time
import subprocess

class FaceRecognitionApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Face Recognition Attendance System")
        self.window.geometry("1000x700")
        
        # Fix: Add event handling for dropdown menus
        self.window.update_idletasks()
        self.window.focus_force()
        
        # Initialize camera with error handling
        self.current_cam_index = tk.IntVar(value=0)
        self.video_capture = None
        self.camera_available = False
        self.init_camera()
        
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.data_file = "face_data.pkl"
        self.attendance_file = "attendance.csv"
        self.students_file = "students.csv"
        self.marked_attendance = set()
        
        # Fix: Add queue for attendance marking
        self.attendance_queue = queue.Queue()
        self.is_processing = False
        
        self.load_data()
        self.load_students()
        
        # Create main container
        self.main_container = tk.Frame(window)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left frame for video
        self.left_frame = tk.Frame(self.main_container)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.left_frame, width=640, height=480, bg='black')
        self.canvas.pack(pady=10)
        
        # Right frame for attendance/ID panel
        self.right_frame = tk.Frame(self.main_container, width=300)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        self.right_frame.pack_propagate(False)
        
        # Attendance panel
        self.create_attendance_panel()
        
        # Button frame
        self.btn_frame = tk.Frame(self.left_frame)
        self.btn_frame.pack(pady=10)
        
        # Buttons
        self.register_btn = tk.Button(self.btn_frame, text="Register Face", command=self.register_face, width=15, height=2)
        self.register_btn.grid(row=0, column=0, padx=5)
        
        self.generate_id_btn = tk.Button(self.btn_frame, text="Generate ID Card", command=self.show_id_generator, width=15, height=2)
        self.generate_id_btn.grid(row=0, column=1, padx=5)
        
        self.view_attendance_btn = tk.Button(self.btn_frame, text="View Attendance", command=self.view_attendance, width=15, height=2)
        self.view_attendance_btn.grid(row=0, column=2, padx=5)
        
        self.quit_btn = tk.Button(self.btn_frame, text="Quit", command=self.quit_app, width=15, height=2)
        self.quit_btn.grid(row=0, column=3, padx=5)
        
        # Camera selection frame
        self.cam_frame = tk.Frame(self.left_frame)
        self.cam_frame.pack(pady=5)
        
        tk.Label(self.cam_frame, text="Camera:").pack(side=tk.LEFT, padx=5)
        
        # Fix: Get available cameras properly on Mac
        self.cam_options = self.get_available_cameras_mac()
        self.cam_options_display = [str(cam) for cam in self.cam_options]
        
        # Fix: Create dropdown with proper event binding
        self.cam_var = tk.StringVar(value=str(self.current_cam_index.get()))
        
        # Only show camera dropdown if cameras are available
        if self.cam_options:
            self.cam_menu = tk.OptionMenu(self.cam_frame, self.cam_var, *self.cam_options_display, command=self.change_camera_wrapper)
            self.cam_menu.config(width=10, takefocus=1)
            self.cam_menu.pack(side=tk.LEFT, padx=5)
            
            # Fix: Bind dropdown events
            self.cam_menu.bind('<Button-1>', self.on_dropdown_click)
            self.cam_menu.bind('<FocusIn>', self.on_dropdown_focus)
        else:
            # No cameras available
            tk.Label(self.cam_frame, text="No camera detected", fg="red").pack(side=tk.LEFT, padx=5)
            self.cam_var.set("0")
        
        self.current_frame = None
        self.is_running = True
        self.frame_skip = 0  # Fix: Add frame skipping to reduce CPU usage
        self.update_video()
        
        # Fix: Start attendance queue processor
        self.process_attendance_queue()

    def get_available_cameras_mac(self):
        """Get available cameras specifically for Mac"""
        available_cameras = []
        
        # Fix: On Mac, only check indices 0 and 1 (built-in and external)
        # This prevents the "out of bound" errors
        for i in range(2):  # Only check 0 and 1 on Mac
            try:
                # Quick test without fully opening
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Try to read a frame to confirm it's working
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        available_cameras.append(i)
                    cap.release()
                time.sleep(0.1)
            except Exception as e:
                print(f"Camera {i} error: {e}")
                continue
        
        # If no cameras found, at least add 0 as default
        if not available_cameras:
            # Try once more with default
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

    def on_dropdown_click(self, event):
        """Handle dropdown click to ensure UI responsiveness"""
        self.window.update_idletasks()
        self.window.focus_set()
        return None

    def on_dropdown_focus(self, event):
        """Handle dropdown focus to prevent freezing"""
        self.window.update_idletasks()
        return None

    def change_camera_wrapper(self, selected_value):
        """Wrapper for camera change to handle freezing"""
        # Use after() to prevent freezing
        self.window.after(100, lambda: self.change_camera(int(selected_value)))

    def init_camera(self):
        """Initialize camera with better error handling for Mac"""
        try:
            if self.video_capture:
                self.video_capture.release()
                time.sleep(0.2)  # Longer delay for Mac
            
            # Fix: Only try indices that are likely to exist on Mac
            camera_index = self.current_cam_index.get()
            
            # Limit to 0 or 1 for Mac
            if camera_index > 1:
                camera_index = 0
                self.current_cam_index.set(0)
            
            self.video_capture = cv2.VideoCapture(camera_index)
            
            # Fix: Set Mac-specific properties
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if not self.video_capture.isOpened():
                print(f"Failed to open camera {camera_index}, trying default...")
                self.video_capture = cv2.VideoCapture(0)
                self.current_cam_index.set(0)
                
            # Test if we can read a frame
            if self.video_capture.isOpened():
                ret, frame = self.video_capture.read()
                if not ret or frame is None:
                    print("Camera opened but cannot read frames")
                    self.camera_available = False
                else:
                    self.camera_available = True
            else:
                self.camera_available = False
                
        except Exception as e:
            print(f"Camera initialization error: {e}")
            self.video_capture = None
            self.camera_available = False

    def get_available_cameras(self):
        """Detect available cameras - limited to 2 for Mac"""
        available_cameras = []
        
        # Fix: Only check indices 0 and 1 to avoid OpenCV errors
        for i in range(2):  # Only check first 2 cameras
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Try to read a frame
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        available_cameras.append(i)
                    cap.release()
                time.sleep(0.1)
            except:
                pass
        
        # Always include 0 as fallback
        if not available_cameras:
            available_cameras = [0]
            
        return available_cameras

    def create_attendance_panel(self):
        """Create the attendance display panel"""
        # Title
        tk.Label(self.right_frame, text="Today's Attendance", 
                font=("Arial", 16, "bold")).pack(pady=10)
        
        # Treeview for attendance
        columns = ("Name", "Time")
        self.attendance_tree = ttk.Treeview(self.right_frame, columns=columns, 
                                           show="headings", height=15)
        self.attendance_tree.heading("Name", text="Name")
        self.attendance_tree.heading("Time", text="Time")
        self.attendance_tree.column("Name", width=120)
        self.attendance_tree.column("Time", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.right_frame, orient=tk.VERTICAL, 
                                  command=self.attendance_tree.yview)
        self.attendance_tree.configure(yscrollcommand=scrollbar.set)
        
        self.attendance_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh button
        tk.Button(self.right_frame, text="Refresh", command=self.refresh_attendance_display,
                 width=15).pack(pady=5)
        
        # Load today's attendance
        self.refresh_attendance_display()

    def refresh_attendance_display(self):
        """Refresh the attendance display"""
        # Clear current items
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
        
        # Load today's attendance
        if os.path.exists(self.attendance_file):
            today = datetime.now().strftime("%Y-%m-%d")
            try:
                with open(self.attendance_file, 'r') as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader:
                        if len(row) >= 2:
                            name, time_str = row[0], row[1]
                            if time_str.startswith(today):
                                self.attendance_tree.insert("", tk.END, values=(name, time_str))
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

    def change_camera(self, selected_index):
        """Change camera with better error handling for Mac"""
        try:
            if self.video_capture:
                self.video_capture.release()
                time.sleep(0.2)  # Longer delay for Mac
            
            # Fix: Limit to valid indices on Mac
            if selected_index > 1:
                selected_index = 0
            
            self.current_cam_index.set(selected_index)
            self.video_capture = cv2.VideoCapture(selected_index)
            
            # Set Mac-specific properties
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if not self.video_capture.isOpened():
                messagebox.showerror("Camera Error", f"Camera {selected_index} is not available.")
                self.video_capture = cv2.VideoCapture(0)
                self.current_cam_index.set(0)
                self.cam_var.set("0")
            
            # Test frame read
            ret, frame = self.video_capture.read()
            if not ret or frame is None:
                print("Camera opened but cannot read frames")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change camera: {str(e)}")
            self.video_capture = cv2.VideoCapture(0)
            self.current_cam_index.set(0)
            self.cam_var.set("0")

    def load_data(self):
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
        try:
            with open(self.data_file, 'wb') as f:
                pickle.dump({'encodings': self.known_face_encodings, 'names': self.known_face_names}, f)
        except:
            pass

    def mark_attendance(self, name):
        """Add attendance to queue instead of processing immediately"""
        if name not in self.marked_attendance and name != "Unknown":
            self.attendance_queue.put(name)

    def process_attendance_queue(self):
        """Process attendance queue in main thread"""
        try:
            while not self.attendance_queue.empty():
                name = self.attendance_queue.get_nowait()
                if name not in self.marked_attendance:
                    now = datetime.now()
                    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
                    file_exists = os.path.isfile(self.attendance_file)
                    
                    try:
                        with open(self.attendance_file, 'a', newline='') as f:
                            writer = csv.writer(f)
                            if not file_exists:
                                writer.writerow(["Name", "Time"])
                            writer.writerow([name, dt_string])
                    except:
                        pass
                        
                    self.marked_attendance.add(name)
                    self.refresh_attendance_display()
        except:
            pass
        
        # Schedule next check
        self.window.after(1000, self.process_attendance_queue)

    def update_video(self):
        if not self.is_running:
            return
        
        # Fix: Frame skipping to reduce CPU usage and prevent freezing
        self.frame_skip += 1
        if self.frame_skip % 3 != 0:  # Process every 3rd frame
            if self.is_running:
                self.window.after(10, self.update_video)
            return
            
        if self.video_capture and self.video_capture.isOpened() and self.camera_available:
            try:
                ret, frame = self.video_capture.read()
                if ret and frame is not None:
                    self.current_frame = frame.copy()
                    
                    # Process only every few frames for face recognition to save CPU
                    if self.frame_skip % 6 == 0:  # Face recognition every 6th frame
                        try:
                            # Resize frame for faster processing
                            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                            
                            # Find faces
                            face_locations = face_recognition.face_locations(rgb_small_frame)
                            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                            
                            # Process each face
                            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                                if self.known_face_encodings:
                                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                                    name = "Unknown"
                                    
                                    if True in matches:
                                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                                        best_match_index = np.argmin(face_distances)
                                        if matches[best_match_index]:
                                            name = self.known_face_names[best_match_index]
                                            if name not in self.marked_attendance:
                                                self.attendance_queue.put(name)
                                    
                                    # Scale back face locations
                                    top *= 4
                                    right *= 4
                                    bottom *= 4
                                    left *= 4
                                    
                                    # Draw rectangle and name
                                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                                    cv2.putText(frame, name, (left + 6, bottom - 6), 
                                              cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
                        except Exception as e:
                            print(f"Face recognition error: {e}")

                    # Convert for tkinter
                    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                    img = Image.fromarray(cv2image)
                    self.photo = ImageTk.PhotoImage(image=img)
                    self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
                else:
                    # Show error message on canvas
                    self.show_camera_error()
                    
            except Exception as e:
                print(f"Video update error: {e}")
                self.show_camera_error()
        else:
            # Show camera unavailable message
            self.show_camera_error()
        
        if self.is_running:
            self.window.after(10, self.update_video)

    def show_camera_error(self):
        """Show camera error message on canvas"""
        self.canvas.delete("all")
        self.canvas.create_text(320, 240, text="Camera Not Available\nPlease check your camera connection", 
                               fill="white", font=("Arial", 16), justify=tk.CENTER)

    def register_face(self):
        if self.current_frame is not None:
            # Pause video temporarily for registration
            self.is_processing = True
            
            name = simpledialog.askstring("Input", "Enter name for the new face:")
            if name:
                if name in self.known_face_names:
                    messagebox.showerror("Error", "This name is already registered!")
                    self.is_processing = False
                    return
                    
                rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                
                if len(face_locations) == 1:
                    face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
                    self.known_face_encodings.append(face_encoding)
                    self.known_face_names.append(name)
                    self.known_face_ids.append('')
                    self.save_data()
                    
                    self.collect_student_details(name)
                    
                elif len(face_locations) == 0:
                    messagebox.showerror("Error", "No face detected. Please try again.")
                else:
                    messagebox.showerror("Error", "Multiple faces detected. Please ensure only one face is in the frame.")
            
            self.is_processing = False

    def collect_student_details(self, name):
        """Collect additional details for ID card"""
        details_window = tk.Toplevel(self.window)
        details_window.title("Student Details")
        details_window.geometry("300x250")
        details_window.transient(self.window)
        details_window.grab_set()
        
        tk.Label(details_window, text="Enter Student Details", font=("Arial", 14, "bold")).pack(pady=10)
        
        tk.Label(details_window, text="Student ID:").pack()
        student_id = tk.Entry(details_window, width=30)
        student_id.pack(pady=5)
        student_id.focus_set()
        
        tk.Label(details_window, text="Course:").pack()
        course = tk.Entry(details_window, width=30)
        course.pack(pady=5)
        
        def save_details():
            if student_id.get() and course.get():
                index = self.known_face_names.index(name)
                self.known_face_ids[index] = student_id.get()
                self.save_student(name, student_id.get(), course.get())
                messagebox.showinfo("Success", f"Student details saved for {name}")
                details_window.destroy()
                
                if messagebox.askyesno("Generate ID", "Do you want to generate ID card now?"):
                    self.generate_id_card(name)
            else:
                messagebox.showerror("Error", "Please fill all fields")
        
        tk.Button(details_window, text="Save", command=save_details, width=15).pack(pady=20)

    def show_id_generator(self):
        """Show ID generator window"""
        if not self.known_face_names:
            messagebox.showinfo("Info", "No registered faces found. Please register first.")
            return
            
        select_window = tk.Toplevel(self.window)
        select_window.title("Select Student")
        select_window.geometry("300x200")
        select_window.transient(self.window)
        select_window.grab_set()
        
        tk.Label(select_window, text="Select Student for ID Card", font=("Arial", 12, "bold")).pack(pady=10)
        
        selected_student = tk.StringVar()
        student_menu = ttk.Combobox(select_window, textvariable=selected_student, 
                                   values=self.known_face_names, state="readonly", width=25)
        student_menu.pack(pady=10)
        student_menu.focus_set()
        
        def generate():
            if selected_student.get():
                self.generate_id_card(selected_student.get())
                select_window.destroy()
            else:
                messagebox.showerror("Error", "Please select a student")
        
        tk.Button(select_window, text="Generate ID Card", command=generate, width=15).pack(pady=20)

    def generate_id_card(self, name):
        """Generate ID card based on Canva design"""
        try:
            index = self.known_face_names.index(name)
            student_id = self.known_face_ids[index] if index < len(self.known_face_ids) else ""
            
            if not student_id:
                student_id = simpledialog.askstring("Student ID", f"Enter Student ID for {name}:")
                if not student_id:
                    return
                self.known_face_ids[index] = student_id
            
            card_width = 600
            card_height = 350
            
            card = Image.new('RGB', (card_width, card_height), '#1a237e')
            
            for i in range(card_height):
                r = int(26 + (i * 0.1))
                g = int(35 + (i * 0.1))
                b = int(126 + (i * 0.2))
                for x in range(card_width):
                    if x < card_width // 2:
                        card.putpixel((x, i), (min(r, 255), min(g, 255), min(b, 255)))
                    else:
                        card.putpixel((x, i), (min(r+10, 255), min(g+15, 255), min(b+20, 255)))
            
            draw = ImageDraw.Draw(card)
            
            draw.rectangle([20, 20, card_width-20, card_height-20], fill='white', outline='#ffd700', width=3)
            
            draw.rectangle([30, 30, card_width-30, 80], fill='#1a237e')
            draw.text((card_width//2, 55), "STUDENT ID CARD", fill='#ffd700', anchor="mm", font=self.get_font(24, bold=True))
            
            draw.rectangle([50, 100, 150, 200], fill='#e0e0e0', outline='#1a237e', width=2)
            draw.text((100, 150), "PHOTO", fill='#666', anchor="mm")
            
            draw.text((250, 120), f"Name:", fill='#333', font=self.get_font(14))
            draw.text((250, 120), f"{name}", fill='#1a237e', font=self.get_font(14, bold=True))
            
            draw.text((250, 150), f"ID:", fill='#333', font=self.get_font(14))
            draw.text((250, 150), f"{student_id}", fill='#1a237e', font=self.get_font(14, bold=True))
            
            course = self.get_student_course(name)
            if course:
                draw.text((250, 180), f"Course:", fill='#333', font=self.get_font(14))
                draw.text((250, 180), f"{course}", fill='#1a237e', font=self.get_font(14, bold=True))
            
            today = datetime.now().strftime("%d/%m/%Y")
            draw.text((250, 230), f"Issued:", fill='#333', font=self.get_font(12))
            draw.text((250, 230), f"{today}", fill='#1a237e', font=self.get_font(12))
            
            draw.line([250, 280, 450, 280], fill='#333', width=2)
            draw.text((350, 290), "Authorized Signature", fill='#666', anchor="mm", font=self.get_font(10))
            
            draw.ellipse([card_width-80, card_height-80, card_width-30, card_height-30], 
                        outline='#ffd700', width=3)
            
            filename = f"ID_Card_{name}_{student_id}.png"
            card.save(filename)
            
            self.display_id_card(card, name)
            
            messagebox.showinfo("Success", f"ID Card generated and saved as {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate ID card: {str(e)}")

    def get_font(self, size, bold=False):
        """Get font for ID card"""
        try:
            if platform.system() == "Windows":
                font_name = "arialbd.ttf" if bold else "arial.ttf"
                return ImageFont.truetype(font_name, size)
            else:
                if platform.system() == "Darwin":  # Mac
                    # Try different Mac font paths
                    font_paths = [
                        "/System/Library/Fonts/Helvetica.ttc",
                        "/Library/Fonts/Arial.ttf",
                        "/System/Library/Fonts/Supplemental/Arial.ttf"
                    ]
                    for font_path in font_paths:
                        try:
                            return ImageFont.truetype(font_path, size)
                        except:
                            continue
                else:  # Linux
                    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                    try:
                        return ImageFont.truetype(font_path, size)
                    except:
                        pass
        except:
            pass
        return ImageFont.load_default()

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

    def display_id_card(self, card_image, name):
        """Display ID card in a new window"""
        display_window = tk.Toplevel(self.window)
        display_window.title(f"ID Card - {name}")
        display_window.geometry("620x420")
        display_window.transient(self.window)
        
        card_image.thumbnail((600, 350))
        photo = ImageTk.PhotoImage(card_image)
        
        label = tk.Label(display_window, image=photo)
        label.image = photo
        label.pack(pady=20)
        
        tk.Button(display_window, text="Close", command=display_window.destroy, width=15).pack(pady=10)

    def view_attendance(self):
        """View full attendance report"""
        report_window = tk.Toplevel(self.window)
        report_window.title("Attendance Report")
        report_window.geometry("600x400")
        report_window.transient(self.window)
        
        columns = ("Name", "Date", "Time")
        tree = ttk.Treeview(report_window, columns=columns, show="headings")
        tree.heading("Name", text="Name")
        tree.heading("Date", text="Date")
        tree.heading("Time", text="Time")
        
        tree.column("Name", width=150)
        tree.column("Date", width=150)
        tree.column("Time", width=150)
        
        scrollbar = ttk.Scrollbar(report_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        if os.path.exists(self.attendance_file):
            try:
                with open(self.attendance_file, 'r') as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader:
                        if len(row) >= 2:
                            name, datetime_str = row[0], row[1]
                            try:
                                dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                                date_str = dt.strftime("%Y-%m-%d")
                                time_str = dt.strftime("%H:%M:%S")
                                tree.insert("", tk.END, values=(name, date_str, time_str))
                            except:
                                tree.insert("", tk.END, values=(name, datetime_str, ""))
            except:
                pass
        
        def export_attendance():
            filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Name", "Date", "Time"])
                    for item in tree.get_children():
                        writer.writerow(tree.item(item)['values'])
                messagebox.showinfo("Success", f"Report exported as {filename}")
            except:
                messagebox.showerror("Error", "Failed to export report")
        
        tk.Button(report_window, text="Export to CSV", command=export_attendance, width=15).pack(pady=10)

    def quit_app(self):
        self.is_running = False
        if self.video_capture:
            self.video_capture.release()
        self.window.quit()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()
