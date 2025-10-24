import tkinter as tk
from tkinter import messagebox
import subprocess
import webbrowser
import tempfile
import os
import time
import winreg
import ctypes
import smtplib, ssl, random, string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image, ImageTk
import requests
import io
import psycopg2
import cv2
import numpy as np
from io import BytesIO

print("📁 Videos are being saved in:", os.getcwd())

# ----------------- Email & DB Setup -----------------
SENDER_EMAIL = "23wh1a1206@bvrithyderabad.edu.in"
SENDER_APP_PASSWORD = "your-app-pass"
log_file = "camera_log.txt"
password = None
RECIPIENT_EMAIL = "23wh1a1206@bvrithyderabad.edu.in"

DB_HOST = "localhost"
DB_NAME = "webcam_security"
DB_USER = "postgres"
DB_PASS = "postgres"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def ensure_face_table():
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS faces (
        id SERIAL PRIMARY KEY,
        name TEXT,
        image BYTEA,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY,
        action TEXT,
        log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS password_table (
        id SERIAL PRIMARY KEY,
        password TEXT,
        recipient_email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit(); cur.close(); conn.close()

ensure_face_table()

# ---------------- Log Action ----------------
def log_action(action):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO logs (action) VALUES (%s)", (action,))
    conn.commit()
    cur.close()
    conn.close()
    with open(log_file, "a") as log:
        log.write(f"{action} - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

# ---------------- Password Utils ----------------
def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def send_password_via_email(recipient_email, new_password):
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = "🔒 Webcam Password"
        text = f"Hello,\n\nwebcam security password is: {new_password}\nKeep it safe.\nRegards, WebCam Security Team"
        html = f"""
        <p>Hello,</p><p>This is your new, one-time-use password for the *Webcam Security System* on your device:</p>
        <div>
        <p><strong>Password:</strong><br><b>{new_password}</b></p>
        </div>
        <p>ACTION REQUIRED: For your security, please use this password *immediately* to log in and manage your webcam settings.</p>
        <p>This password is for single use. Keep it secure and do not share it. If you did not request this password, please contact our support team immediately.</p>
        <p>Best regards,<br><strong>WebCam Security Team</strong></p>
      """
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            smtp.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send email: {e}")
        return False

def set_password():
    def save_manual_password():
        new_pw = new_pw_entry.get()
        conf_pw = conf_pw_entry.get()
        if not new_pw:
            error_label.config(text="Password cannot be empty.")
            return
        if new_pw != conf_pw:
            error_label.config(text="Passwords do not match.")
            return
        set_global_password(new_pw, None)
        pw_window.destroy()
        messagebox.showinfo("Success", f"Password set successfully.")

    def generate_and_send():
        new_pw = generate_random_password()
        def ask_email():
            recipient = email_entry.get().strip()
            if not recipient:
                error_label_popup.config(text="Recipient email cannot be empty.")
                return
            if send_password_via_email(recipient, new_pw):
                set_global_password(new_pw, recipient)
                email_window.destroy()
                pw_window.destroy()
                messagebox.showinfo("Success", f"Password sent to {recipient}")
        email_window = tk.Toplevel(root)
        email_window.title("Recipient Email")
        email_window.geometry("300x150")
        tk.Label(email_window, text="Enter Recipient Email:").pack(pady=10)
        email_entry = tk.Entry(email_window, width=30)
        email_entry.pack(pady=5)
        tk.Button(email_window, text="Send", command=ask_email).pack(pady=10)
        error_label_popup = tk.Label(email_window, text="", fg="red")
        error_label_popup.pack()

    def set_global_password(val, recipient):
        global password
        password = val
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO password_table (password, recipient_email) VALUES (%s, %s)",
            (val, recipient)
        )
        conn.commit()
        cur.close()
        conn.close()

    pw_window = tk.Toplevel(root)
    pw_window.title("Set Password")
    pw_window.geometry("400x300")
    tk.Label(pw_window, text="New Password:").pack(pady=5)
    new_pw_entry = tk.Entry(pw_window, width=30, show="*")
    new_pw_entry.pack(pady=5)
    tk.Label(pw_window, text="Confirm Password:").pack(pady=5)
    conf_pw_entry = tk.Entry(pw_window, width=30, show="*")
    conf_pw_entry.pack(pady=5)
    tk.Button(pw_window, text="Set Password", command=save_manual_password).pack(pady=10)
    tk.Button(pw_window, text="Generate Password", command=generate_and_send).pack(pady=10)
    error_label = tk.Label(pw_window, text="", fg="red")
    error_label.pack()

# ---------------- Camera Functions ----------------
def disable_camera():
    cmd = r'REG ADD "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam" /v Value /t REG_SZ /d Deny /f'
    subprocess.run(cmd, shell=True)
    log_action("Camera Disabled")
    messagebox.showinfo("Notification", "Camera Disabled Successfully")

def enable_camera():
    cmd = r'REG ADD "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam" /v Value /t REG_SZ /d Allow /f'
    subprocess.run(cmd, shell=True)
    log_action("Camera Enabled")
    messagebox.showinfo("Notification", "Camera Enabled Successfully")

def check_status():
    try:
        reg_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"
        )
        value, _ = winreg.QueryValueEx(reg_key, "Value")
        winreg.CloseKey(reg_key)
        status = "Webcam is Disabled" if value == "Deny" else "Webcam is Enabled"
    except FileNotFoundError:
        status = "No registry value found (Default = Enabled)"
    except Exception as e:
        status = f"Error: {e}"
    ctypes.windll.user32.MessageBoxW(None, status, "Webcam Status", 0x40 | 0x1)
def get_recipient_email():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT recipient_email FROM password_table ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row and row[0] else None

def record_intruder(duration=10):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Cannot access camera to record intruder")
        return
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    filename = f"intruder_{time.strftime('%Y%m%d_%H%M%S')}.avi"
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640,480))
    start = time.time()
    while time.time() - start < duration:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
    cap.release()
    out.release()
    log_action(f"Intruder recorded: {filename}")
    messagebox.showwarning("Alert", f"Intruder detected! Video recorded: {filename}")

    # Email the video to the recipient
    recipient_email = get_recipient_email()
    if not recipient_email:
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = "🚨 Intruder Detected - Webcam Security"
        msg.attach(MIMEText("An intruder attempted to access your webcam. Video attached.", "plain"))
        with open(filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(filename)}")
        msg.attach(part)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            smtp.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        log_action(f"Intruder video emailed to {recipient_email}")
    except Exception as e:
        messagebox.showerror("Email Error", f"Failed to send intruder video: {e}")

def view_logs():
    def check_password_and_open():
        if pw_entry.get() == password:
            pw_window.destroy()
            log_window = tk.Toplevel(root)
            log_window.title("Logs")
            log_window.geometry("400x300")
            text_widget = tk.Text(log_window)
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT action, log_time FROM logs ORDER BY log_time DESC")
            rows = cur.fetchall()
            for action, log_time in rows:
                text_widget.insert(tk.END, f"{log_time} - {action}\n")
            cur.close()
            conn.close()
            text_widget.pack(expand=True, fill="both")
        else:
            error_label.config(text="Incorrect password.")
            record_intruder()
    if not password:
        messagebox.showerror("Error", "No password set! Please set a password first.")
        return
    pw_window = tk.Toplevel(root)
    pw_window.title("Enter Password")
    pw_window.geometry("300x150")
    tk.Label(pw_window, text="Enter Password:").pack(pady=10)
    pw_entry = tk.Entry(pw_window, show="*", width=25)
    pw_entry.pack(pady=5)
    tk.Button(pw_window, text="OK", command=check_password_and_open).pack(pady=10)
    error_label = tk.Label(pw_window, text="", fg="red")
    error_label.pack()

# ---------------- Project Info ----------------
def project_info():
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Project Information</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f2f2f2;
            }
            .container {
                max-width: 1000px;
                margin: 20px auto;
                padding: 20px;
                background-color: #fff;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            h2 {
                text-align: center;
                color: #333;
            }
            h3 {
                margin-top: 30px;
                color: #444;
            }
            p {
                line-height: 1.6;
                color: #333;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                border: 1px solid #ccc;
                padding: 10px;
                text-align: left;
            }
            th {
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Project Information</h2>
            <p>
                This project was developed by <b>Cyber MANS</b> as part of a Cyber-Security Internship.
                This system is designed to provide robust protection for webcam devices against spyware and unauthorized access, significantly securing individuals in the digital world.
            </p>
            <h3>Project Details</h3>
            <table>
                <tr>
                    <th>Project Name</th>
                    <td>Web Cam Spyware Security</td>
                </tr>
                <tr>
                    <th>Project Description</th>
                    <td>This system provides comprehensive webcam security by offering controls to enable/disable the camera and log its status.
                      It integrates user face recognition for secure activation/deactivation, along with multiple password-based authentication methods.</td>
                </tr>
                <tr>
                    <th>Project Start Date</th>
                    <td>30-AUG-2025</td>
                </tr>
                <tr>
                    <th>Project End Date</th>
                    <td>09-OCT-2025</td>
                </tr>
                <tr>
                    <th>Project Status</th>
                    <td>Completed</td>
                </tr>
            </table>
            <h3>Developer Details</h3>
            <table>
                <tr>
                    <th>Name</th>
                    <td>Maryam Fatima</td>
                </tr>
                <tr>
                    <th>Email</th>
                    <td>23wh1a1238@bvrithyderabad.edu.in</td>
                </tr>
            </table>
            <table>
                <tr>
                    <th>Name</th>
                    <td>Ayesha Sultana</td>
                </tr>
                <tr>
                    <th>Email</th>
                    <td>23wh1a1244@bvrithyderabad.edu.in</td>
                </tr>
            </table>
            <table>
                <tr>
                    <th>Name</th>
                    <td>Nishat Unnisa</td>
                </tr>
                <tr>
                    <th>Email</th>
                    <td>23wh1a1253@bvrithyderabad.edu.in</td>
                </tr>
            </table>
            <table>
                <tr>
                    <th>Name</th>
                    <td>R.Sristi</td>
                </tr>
                <tr>
                    <th>Email</th>
                    <td>23wh1a1206@bvrithyderabad.edu.in</td>
                </tr>
            </table>
            <h3>Company Details</h3>
            <table>
                <tr>
                    <th>Company</th>
                    <td>Suparaja technology</td>
                </tr>
                <tr>
                    <th>Contact Mail</th>
                    <td>contact@supraja.com</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as temp_file:
        temp_file.write(html_code)
        temp_file_path = temp_file.name
    webbrowser.open('file://' + os.path.realpath(temp_file_path))
# ---------------- FACE RECOGNITION ----------------
def store_face_in_db(name, face_img_np):
    buf = BytesIO()
    Image.fromarray(face_img_np).save(buf, format='PNG')
    img_bytes = buf.getvalue()
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO faces (name, image) VALUES (%s, %s)", (name, psycopg2.Binary(img_bytes)))
    conn.commit(); cur.close(); conn.close()

def train_recognizer():
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT id, image FROM faces")
    rows = cur.fetchall(); cur.close(); conn.close()
    if not rows:
        return None, {}
    faces = []; labels = []
    for rid, img_bytes in rows:
        img = Image.open(BytesIO(img_bytes)).convert('L')
        img_np = np.array(img, dtype='uint8')
        img_resized = cv2.resize(img_np, (200,200))
        faces.append(img_resized)
        labels.append(int(rid))
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
    except Exception as e:
        messagebox.showerror("Error", "LBPH recognizer not available. Install opencv-contrib-python.")
        return None, {}
    recognizer.train(faces, np.array(labels))
    return recognizer, {r[0]: r[1] for r in rows}

def enroll_face():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Cannot open camera")
        return
    top = tk.Toplevel(root)
    top.title("Enroll Face")
    top.geometry("350x140")
    tk.Label(top, text="Name:").pack(pady=5)
    name_entry = tk.Entry(top)
    name_entry.pack()
    tk.Label(top, text="Preview will open. Press 'c' to capture or 'q' to cancel.").pack(pady=8)
    def start_preview():
        name = name_entry.get().strip() or "unknown"
        preview_name = "Enroll Preview - press c to capture, q to cancel"
        cv2.namedWindow(preview_name)
        captured = False
        while True:
            ret, frame = cap.read()
            if not ret: break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
            cv2.imshow(preview_name, frame)
            k = cv2.waitKey(1) & 0xFF
            if k == ord('c'):
                if len(faces) == 0:
                    messagebox.showerror("Error", "No face detected to capture")
                    continue
                x, y, w, h = faces[0]
                face_img = gray[y:y+h, x:x+w]
                face_img = cv2.resize(face_img, (200,200))
                store_face_in_db(name, face_img)
                messagebox.showinfo("OK", f"Enrolled: {name}")
                captured = True
                break
            if k == ord('q'):
                break
        cap.release(); cv2.destroyAllWindows()
        top.destroy()
        return captured
    tk.Button(top, text="Start Preview & Capture (press c)", command=start_preview).pack(pady=6)
    tk.Button(top, text="Cancel", command=lambda: [cap.release(), cv2.destroyAllWindows(), top.destroy()]).pack()
    top.transient(root); top.grab_set()

def auth_choice(action_callback):
    win = tk.Toplevel(root)
    win.title("Unlock Method")
    win.geometry("320x140")
    tk.Label(win, text="Choose unlock method:", font=("Helvetica",12,"bold")).pack(pady=8)
    btn_frame = tk.Frame(win); btn_frame.pack(pady=5)
    def use_password():
        win.destroy()
        require_password(action_callback)
    def use_face():
        win.destroy()
        recognize_face(action_callback)
    pw_btn = tk.Button(btn_frame, text="Password Unlock", width=14, command=use_password)
    pw_btn.grid(row=0, column=0, padx=6)
    face_btn = tk.Button(btn_frame, text="Face Unlock", width=14, command=use_face)
    face_btn.grid(row=0, column=1, padx=6)
    if not password:
        pw_btn.config(state="disabled")
        tk.Label(win, text="(No password set — set a password to enable password unlock)", fg="red", wraplength=300).pack(pady=6)

def recognize_face(action_callback, confidence_threshold=70, timeout=12):
    trained = train_recognizer()
    if trained is None or trained[0] is None:
        messagebox.showerror("Error", "No enrolled faces or recognizer unavailable")
        return
    recognizer, _ = trained
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT id, name FROM faces"); rows = cur.fetchall(); cur.close(); conn.close()
    id_name = {r[0]: r[1] for r in rows}
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Cannot open camera"); return
    start = time.time(); matched_name = None
    preview_name = "Face Authentication - show face to camera (esc to cancel)"
    cv2.namedWindow(preview_name)
    while time.time() - start < timeout:
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (200,200))
            try:
                label, conf = recognizer.predict(face)
            except Exception:
                continue
            if conf < confidence_threshold:
                matched_name = id_name.get(label, "Unknown")
                cv2.putText(frame, f"{matched_name} ({int(conf)})", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                break
            else:
                cv2.putText(frame, f"Unknown ({int(conf)})", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,0,255), 2)
        cv2.imshow(preview_name, frame)
        k = cv2.waitKey(1) & 0xFF
        if matched_name or k == 27:
            break
    cap.release(); cv2.destroyAllWindows()
    if matched_name:
        log_action(f"Face matched: {matched_name}")
        action_callback()
    else:
        record_intruder()
        messagebox.showerror("Error", "Face not recognized or timed out")

def require_password(action_callback):
    if not password:
        messagebox.showerror("Error", "No password set! Please set a password first.")
        return
    def check_password():
        if pw_entry.get() == password:
            pw_window.destroy()
            action_callback()
        else:
            error_label.config(text="Incorrect password.")
            record_intruder()
    pw_window = tk.Toplevel(root)
    pw_window.title("Enter Password")
    pw_window.geometry("300x150")
    tk.Label(pw_window, text="Enter Password:").pack(pady=10)
    pw_entry = tk.Entry(pw_window, show="*", width=25)
    pw_entry.pack(pady=5)
    tk.Button(pw_window, text="OK", command=check_password).pack(pady=10)
    error_label = tk.Label(pw_window, text="", fg="red")
    error_label.pack()

# ---------------- Tkinter UI ----------------
root = tk.Tk()
root.title("Web Cam Security")
root.geometry("720x720")
w,h=720,720
sw,sh=root.winfo_screenwidth(),root.winfo_screenheight()
x,y=int((sw/2)-(w/2)),int((sh/2)-(h/2))
root.geometry(f"{w}x{h}+{x}+{y}")

bg_colors=["#0d0d0d","#1a0000","#0d0d0d","#330000"]
ci=0
def pulse_bg():
    global ci
    root.configure(bg=bg_colors[ci])
    ci=(ci+1)%len(bg_colors)
    root.after(250,pulse_bg)
pulse_bg()

banner=tk.Frame(root,bg="#0d0d0d",height=120)
banner.pack(fill="x",pady=15)
tk.Label(banner,text="WebCam Spyware Security",font=("Courier",28,"bold"),fg="#ff1a1a",bg="#0d0d0d").pack(expand=True)

def load_image_from_url(url,size=(120,120)):
    try:
        r=requests.get(url); r.raise_for_status(); img=Image.open(io.BytesIO(r.content)).resize(size)
        return ImageTk.PhotoImage(img)
    except: return None
photo=load_image_from_url("https://tse4.mm.bing.net/th/id/OIP.d8wWm-r9PgjFNrZvdZ0b0gHaG2?pid=Api&P=0&h=180")
if photo: tk.Label(root,image=photo,bg="#0d0d0d").pack(pady=20)

def create_glow_button(master,text,command,bg,fg="white"):
    btn=tk.Button(master,text=text,font=("Helvetica",14,"bold"),bg=bg,fg=fg,command=command,relief="raised",bd=4)
    def on_enter(e): btn.config(bg="#ff3333",fg="#000",relief="groove",bd=6)
    def on_leave(e): btn.config(bg=bg,fg=fg,relief="raised",bd=4)
    btn.bind("<Enter>",on_enter); btn.bind("<Leave>",on_leave); return btn

create_glow_button(root,"Project Info",project_info,bg="#990000").pack(pady=10)
frame2=tk.Frame(root,bg="#0d0d0d"); frame2.pack(pady=20,fill="x")
create_glow_button(frame2,"Disable Camera",lambda:auth_choice(disable_camera),bg="#ff1a1a").pack(fill="x",padx=50,pady=10)
create_glow_button(frame2,"Enable Camera",lambda:auth_choice(enable_camera),bg="#ff1a1a").pack(fill="x",padx=50,pady=10)

frame3=tk.Frame(root,bg="#0d0d0d"); frame3.pack(pady=10,fill="x")
row1=tk.Frame(frame3,bg="#0d0d0d"); row1.pack(fill="x",pady=2)
row2=tk.Frame(frame3,bg="#0d0d0d"); row2.pack(fill="x",pady=2)

create_glow_button(row1,"View Logs",view_logs,bg="#660000").pack(side="left",expand=True,padx=10)
create_glow_button(row1,"Check Status",check_status,bg="#660000").pack(side="left",expand=True,padx=10)
create_glow_button(row1,"Set Password",set_password,bg="#660000").pack(side="left",expand=True,padx=10)

create_glow_button(row2,"Enroll Face",enroll_face,bg="#004400").pack(side="left",expand=True,padx=10)
create_glow_button(row2,"Face Auth Disable",lambda:recognize_face(disable_camera),bg="#004400").pack(side="left",expand=True,padx=10)
create_glow_button(row2,"Face Auth Enable",lambda:recognize_face(enable_camera),bg="#004400").pack(side="left",expand=True,padx=10)

root.mainloop()

