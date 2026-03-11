import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="", 
        database="face_attendance_system"
    )
    return conn
