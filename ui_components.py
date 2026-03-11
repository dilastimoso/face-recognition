import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

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
        
    def update_frame(self, frame):
        """Update canvas with new frame"""
        if frame is not None:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            self.photo = ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
    
    def show_error(self, message):
        """Show error message on canvas"""
        self.canvas.delete("all")
        self.canvas.create_text(320, 240, text=message, 
                               fill="white", font=("Arial", 16), justify=tk.CENTER)
