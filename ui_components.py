import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2  # Import at module level

class AttendancePanel:
    def __init__(self, parent, refresh_callback):
        self.parent = parent
        self.refresh_callback = refresh_callback
        self.tree = None
        self.create_panel()
        
    def create_panel(self):
        """Create the attendance display panel"""
        tk.Label(self.parent, text="Today's Attendance", 
                font=("Arial", 16, "bold")).pack(pady=10)
        
        columns = ("Name", "Time")
        self.tree = ttk.Treeview(self.parent, columns=columns, 
                                 show="headings", height=15)
        self.tree.heading("Name", text="Name")
        self.tree.heading("Time", text="Time")
        self.tree.column("Name", width=120)
        self.tree.column("Time", width=150)
        
        scrollbar = ttk.Scrollbar(self.parent, orient=tk.VERTICAL, 
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Button(self.parent, text="Refresh", command=self.refresh_callback,
                 width=15).pack(pady=5)
    
    def update_display(self, attendance_data):
        """Update the attendance display"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for name, time_str in attendance_data:
            self.tree.insert("", tk.END, values=(name, time_str))

class VideoCanvas:
    def __init__(self, parent, width=640, height=480):
        self.canvas = tk.Canvas(parent, width=width, height=height, bg='black')
        self.canvas.pack(pady=10)
        self.photo = None
        # Don't store cv2 as instance variable, we'll import it directly in the method
        
    def update_frame(self, frame):
        """Update canvas with new frame"""
        if frame is not None:
            try:
                # Import cv2 directly inside the method to ensure it's in scope
                import cv2
                from PIL import Image, ImageTk
                
                # Convert the frame
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                img = Image.fromarray(cv2image)
                self.photo = ImageTk.PhotoImage(image=img)
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            except ImportError as e:
                print(f"Import error in update_frame: {e}")
                self.show_error(f"Import error: {str(e)}")
            except Exception as e:
                print(f"Error updating frame: {e}")
                self.show_error(f"Error: {str(e)}")
    
    def show_error(self, message):
        """Show error message on canvas"""
        self.canvas.delete("all")
        self.canvas.create_text(320, 240, text=message, 
                               fill="white", font=("Arial", 16), justify=tk.CENTER)
