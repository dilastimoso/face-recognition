import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import cv2
from PIL import Image, ImageTk
import queue
import time
import os
import csv
import sys
import traceback
from datetime import datetime

# Add the current directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Verify cv2 is imported and working
try:
    print(f"OpenCV version: {cv2.__version__}")
    test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    test_converted = cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGBA)
    print("OpenCV is working properly")
except Exception as e:
    print(f"OpenCV initialization error: {e}")

from camera_handler import CameraHandler
from data_manager import DataManager
from face_processor import FaceProcessor
from id_card_generator import IDCardGenerator
from ui_components import AttendancePanel, VideoCanvas

class FaceRecognitionApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Face Recognition Attendance System")
        self.window.geometry("1000x700")
        
        # Initialize components
        self.camera_handler = CameraHandler()
        self.data_manager = DataManager()
        self.attendance_queue = queue.Queue()
        self.face_processor = FaceProcessor(self.data_manager, self.attendance_queue)
        self.id_generator = IDCardGenerator(self.data_manager)
        
        # UI event handling
        self.window.update_idletasks()
        self.window.focus_force()
        
        # Initialize camera
        self.current_cam_index = tk.IntVar(value=0)
        self.camera_handler.init_camera(self.current_cam_index.get())
        
        # Load data
        self.data_manager.load_data()
        self.data_manager.load_students()
        
        # Create UI
        self.create_ui()
        
        # State variables
        self.is_running = True
        self.frame_skip = 0
        self.is_processing = False
        self.error_count = 0
        self.consecutive_errors = 0
        
        # Start processes
        self.update_video()
        self.process_attendance_queue()

    def create_ui(self):
        """Create the main UI"""
        # Main container
        self.main_container = tk.Frame(self.window)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left frame for video
        self.left_frame = tk.Frame(self.main_container)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Video canvas
        self.canvas = VideoCanvas(self.left_frame)
        
        # Right frame for attendance
        self.right_frame = tk.Frame(self.main_container, width=300)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        self.right_frame.pack_propagate(False)
        
        # Attendance panel
        self.attendance_panel = AttendancePanel(self.right_frame, self.refresh_attendance_display)
        
        # Button frame
        self.create_button_frame()
        
        # Camera selection
        self.create_camera_selection()

    def create_button_frame(self):
        """Create button frame with all buttons"""
        self.btn_frame = tk.Frame(self.left_frame)
        self.btn_frame.pack(pady=10)
        
        buttons = [
            ("Register Face", self.register_face),
            ("Generate ID Card", self.show_id_generator),
            ("View Attendance", self.view_attendance),
            ("Quit", self.quit_app)
        ]
        
        for i, (text, command) in enumerate(buttons):
            btn = tk.Button(self.btn_frame, text=text, command=command, 
                          width=15, height=2)
            btn.grid(row=0, column=i, padx=5)

    def create_camera_selection(self):
        """Create camera selection dropdown"""
        self.cam_frame = tk.Frame(self.left_frame)
        self.cam_frame.pack(pady=5)
        
        tk.Label(self.cam_frame, text="Camera:").pack(side=tk.LEFT, padx=5)
        
        self.cam_options = self.camera_handler.get_available_cameras_mac()
        self.cam_options_display = [str(cam) for cam in self.cam_options]
        self.cam_var = tk.StringVar(value=str(self.current_cam_index.get()))
        
        if self.cam_options:
            self.cam_menu = tk.OptionMenu(self.cam_frame, self.cam_var, 
                                         *self.cam_options_display, 
                                         command=self.change_camera_wrapper)
            self.cam_menu.config(width=10, takefocus=1)
            self.cam_menu.pack(side=tk.LEFT, padx=5)
            
            self.cam_menu.bind('<Button-1>', self.on_dropdown_click)
            self.cam_menu.bind('<FocusIn>', self.on_dropdown_focus)
        else:
            tk.Label(self.cam_frame, text="No camera detected", 
                    fg="red").pack(side=tk.LEFT, padx=5)
            self.cam_var.set("0")

    def on_dropdown_click(self, event):
        """Handle dropdown click"""
        self.window.update_idletasks()
        self.window.focus_set()
        return None

    def on_dropdown_focus(self, event):
        """Handle dropdown focus"""
        self.window.update_idletasks()
        return None

    def change_camera_wrapper(self, selected_value):
        """Wrapper for camera change"""
        self.window.after(100, lambda: self.change_camera(int(selected_value)))

    def change_camera(self, selected_index):
        """Change camera"""
        success, message = self.camera_handler.change_camera(selected_index)
        if not success:
            messagebox.showerror("Camera Error", message)
            self.camera_handler.init_camera(0)
            self.current_cam_index.set(0)
            self.cam_var.set("0")
        else:
            self.current_cam_index.set(selected_index)

    def refresh_attendance_display(self):
        """Refresh attendance display"""
        attendance_data = []
        if os.path.exists(self.data_manager.attendance_file):
            today = datetime.now().strftime("%Y-%m-%d")
            try:
                with open(self.data_manager.attendance_file, 'r') as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader:
                        if len(row) >= 2:
                            name, time_str = row[0], row[1]
                            if time_str.startswith(today):
                                attendance_data.append((name, time_str))
            except Exception as e:
                print(f"Error reading attendance: {e}")
        
        self.attendance_panel.update_display(attendance_data)

    def process_attendance_queue(self):
        """Process attendance queue"""
        try:
            while not self.attendance_queue.empty():
                name = self.attendance_queue.get_nowait()
                if name not in self.data_manager.marked_attendance:
                    now = datetime.now()
                    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
                    file_exists = os.path.isfile(self.data_manager.attendance_file)
                    
                    try:
                        with open(self.data_manager.attendance_file, 'a', newline='') as f:
                            writer = csv.writer(f)
                            if not file_exists:
                                writer.writerow(["Name", "Time"])
                            writer.writerow([name, dt_string])
                    except Exception as e:
                        print(f"Error writing attendance: {e}")
                    
                    self.data_manager.marked_attendance.add(name)
                    self.refresh_attendance_display()
        except Exception as e:
            print(f"Error processing queue: {e}")
        
        self.window.after(1000, self.process_attendance_queue)

    def update_video(self):
        """Update video feed"""
        if not self.is_running:
            return
        
        try:
            self.frame_skip += 1
            if self.frame_skip % 3 != 0:
                if self.is_running:
                    self.window.after(10, self.update_video)
                return
            
            success, frame = self.camera_handler.read_frame()
            
            if success:
                self.consecutive_errors = 0
                if self.frame_skip % 6 == 0:
                    try:
                        processed_frame = self.face_processor.process_frame(frame)
                    except Exception as e:
                        print(f"Face processing error: {e}")
                        processed_frame = frame
                else:
                    processed_frame = frame
                
                # Direct conversion here as backup if canvas fails
                try:
                    self.canvas.update_frame(processed_frame)
                except Exception as e:
                    print(f"Canvas update error: {e}")
                    self.consecutive_errors += 1
                    
                    # Try direct conversion as fallback
                    try:
                        import cv2
                        from PIL import Image, ImageTk
                        cv2image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGBA)
                        img = Image.fromarray(cv2image)
                        photo = ImageTk.PhotoImage(image=img)
                        self.canvas.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
                        self.canvas.photo = photo  # Keep reference
                        self.consecutive_errors = 0
                    except Exception as e2:
                        print(f"Fallback also failed: {e2}")
                        
                    if self.consecutive_errors > 10:
                        self.canvas.show_error("Display error - check OpenCV installation")
            else:
                self.consecutive_errors += 1
                if self.consecutive_errors > 30:
                    self.canvas.show_error("Camera Not Available\nPlease check your camera connection")
        except Exception as e:
            print(f"Video update error: {e}")
            print(traceback.format_exc())
            self.consecutive_errors += 1
        
        if self.is_running:
            self.window.after(10, self.update_video)

    def register_face(self):
        """Register a new face"""
        if self.camera_handler.current_frame is None:
            messagebox.showerror("Error", "No frame available")
            return
        
        self.is_processing = True
        name = simpledialog.askstring("Input", "Enter name for the new face:")
        
        if name:
            if name in self.data_manager.known_face_names:
                messagebox.showerror("Error", "This name is already registered!")
                self.is_processing = False
                return
            
            success, result = self.face_processor.register_face_from_frame(
                self.camera_handler.current_frame, name
            )
            
            if success:
                self.data_manager.add_face(name, result)
                self.collect_student_details(name)
            else:
                messagebox.showerror("Error", result)
        
        self.is_processing = False

    def collect_student_details(self, name):
        """Collect student details"""
        details_window = tk.Toplevel(self.window)
        details_window.title("Student Details")
        details_window.geometry("300x250")
        details_window.transient(self.window)
        details_window.grab_set()
        
        tk.Label(details_window, text="Enter Student Details", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        tk.Label(details_window, text="Student ID:").pack()
        student_id = tk.Entry(details_window, width=30)
        student_id.pack(pady=5)
        student_id.focus_set()
        
        tk.Label(details_window, text="Course:").pack()
        course = tk.Entry(details_window, width=30)
        course.pack(pady=5)
        
        def save_details():
            if student_id.get() and course.get():
                self.data_manager.update_student_id(name, student_id.get())
                self.data_manager.save_student(name, student_id.get(), course.get())
                messagebox.showinfo("Success", f"Student details saved for {name}")
                details_window.destroy()
                
                if messagebox.askyesno("Generate ID", "Do you want to generate ID card now?"):
                    self.generate_id_card(name)
            else:
                messagebox.showerror("Error", "Please fill all fields")
        
        tk.Button(details_window, text="Save", command=save_details, 
                 width=15).pack(pady=20)

    def show_id_generator(self):
        """Show ID generator window"""
        if not self.data_manager.known_face_names:
            messagebox.showinfo("Info", "No registered faces found. Please register first.")
            return
        
        select_window = tk.Toplevel(self.window)
        select_window.title("Select Student")
        select_window.geometry("300x200")
        select_window.transient(self.window)
        select_window.grab_set()
        
        tk.Label(select_window, text="Select Student for ID Card", 
                font=("Arial", 12, "bold")).pack(pady=10)
        
        selected_student = tk.StringVar()
        student_menu = ttk.Combobox(select_window, textvariable=selected_student, 
                                   values=self.data_manager.known_face_names, 
                                   state="readonly", width=25)
        student_menu.pack(pady=10)
        student_menu.focus_set()
        
        def generate():
            if selected_student.get():
                self.generate_id_card(selected_student.get())
                select_window.destroy()
            else:
                messagebox.showerror("Error", "Please select a student")
        
        tk.Button(select_window, text="Generate ID Card", command=generate, 
                 width=15).pack(pady=20)

    def generate_id_card(self, name):
        """Generate ID card for a student"""
        try:
            index = self.data_manager.known_face_names.index(name)
            student_id = self.data_manager.known_face_ids[index] if index < len(self.data_manager.known_face_ids) else ""
            
            if not student_id:
                student_id = simpledialog.askstring("Student ID", f"Enter Student ID for {name}:")
                if not student_id:
                    return
                self.data_manager.update_student_id(name, student_id)
            
            course = self.data_manager.get_student_course(name)
            card, filename = self.id_generator.generate_id_card(name, student_id, course)
            
            self.display_id_card(card, name)
            messagebox.showinfo("Success", f"ID Card generated and saved as {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate ID card: {str(e)}")

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
        
        tk.Button(display_window, text="Close", command=display_window.destroy, 
                 width=15).pack(pady=10)

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
        
        if os.path.exists(self.data_manager.attendance_file):
            try:
                with open(self.data_manager.attendance_file, 'r') as f:
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
        
        tk.Button(report_window, text="Export to CSV", command=export_attendance, 
                 width=15).pack(pady=10)

    def quit_app(self):
        """Quit the application"""
        self.is_running = False
        self.camera_handler.release_camera()
        self.window.quit()
        self.window.destroy()

if __name__ == "__main__":
    # Add numpy import for testing
    import numpy as np
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()
