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

# ---------------- Email Setup ----------------
SENDER_EMAIL = "23wh1a1206@bvrithyderabad.edu.in"
SENDER_APP_PASSWORD = "rrfb qufz vngd ohln"
log_file = "camera_log.txt"
password = None

# ---------------- Database Setup ----------------
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
        msg["Subject"] = "🔒 Your Secure Webcam Password"

        text = f"Hello,\n\nYour new webcam security password is: {new_password}\nKeep it safe.\nRegards, WebCam Security Team"
        html = f"""
        <html>
        <body>
            <h3>🔒 Webcam Security</h3>
            <p>Your new password is: <b>{new_password}</b></p>
        </body>
        </html>
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

def project_info():
    html_code = "<html><body><h2>Project Info</h2><p>WebCam Security from Spyware</p></body></html>"
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as temp:
        temp.write(html_code)
        temp_path = temp.name
    webbrowser.open('file://' + os.path.realpath(temp_path))

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
create_glow_button(frame2,"Disable Camera",lambda:require_password(disable_camera),bg="#ff1a1a").pack(fill="x",padx=50,pady=10)
create_glow_button(frame2,"Enable Camera",lambda:require_password(enable_camera),bg="#ff1a1a").pack(fill="x",padx=50,pady=10)
frame3=tk.Frame(root,bg="#0d0d0d"); frame3.pack(pady=10,fill="x")
create_glow_button(frame3,"View Logs",view_logs,bg="#660000").pack(side="left",expand=True,padx=10)
create_glow_button(frame3,"Check Status",check_status,bg="#660000").pack(side="left",expand=True,padx=10)
create_glow_button(frame3,"Set Password",set_password,bg="#660000").pack(side="left",expand=True,padx=10)

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
    pw_window = tk.Toplevel(root)
    pw_window.title("Enter Password")
    pw_window.geometry("300x150")
    tk.Label(pw_window, text="Enter Password:").pack(pady=10)
    pw_entry = tk.Entry(pw_window, show="*", width=25)
    pw_entry.pack(pady=5)
    tk.Button(pw_window, text="OK", command=check_password).pack(pady=10)
    error_label = tk.Label(pw_window, text="", fg="red")
    error_label.pack()

root.mainloop()
