import tkinter as tk
from tkinter import messagebox
import subprocess, os, time, ctypes, smtplib, ssl, random, string, webbrowser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image, ImageTk
import requests, io, cv2, numpy as np

# ----------------- Email Setup -----------------
SENDER_EMAIL = "your_email"
SENDER_APP_PASSWORD = "your_password"
log_file = "camera_log.txt"
password = None

# ----------------- Log Action -----------------
def log_action(action):
    with open(log_file, "a") as log:
        log.write(f"{action} - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

# ----------------- Password Utils -----------------
def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def send_password_via_email(recipient_email, new_password):
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = "🔒 Your Secure Webcam Password"
        text = f"Hello,\n\nYour new webcam security password:\nPassword: {new_password}\n\nKeep it safe."
        html = f"<html><body><h2>🔒 Webcam Security</h2><p>Password: <b>{new_password}</b></p></body></html>"
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
    global password
    def save_manual_password():
        new_pw = new_pw_entry.get()
        conf_pw = conf_pw_entry.get()
        if not new_pw:
            error_label.config(text="Password cannot be empty.")
            return
        if new_pw != conf_pw:
            error_label.config(text="Passwords do not match.")
            return
        password = new_pw
        pw_window.destroy()
        messagebox.showinfo("Success", "Password set successfully.")

    def generate_and_send():
        new_pw = generate_random_password()
        def ask_email():
            recipient = email_entry.get().strip()
            if not recipient:
                error_label_popup.config(text="Recipient email cannot be empty.")
                return
            if send_password_via_email(recipient, new_pw):
                global password
                password = new_pw
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

    pw_window = tk.Toplevel(root)
    pw_window.title("Set Password")
    pw_window.geometry("400x250")
    tk.Label(pw_window, text="New Password:").pack(pady=5)
    new_pw_entry = tk.Entry(pw_window, width=30, show="*")
    new_pw_entry.pack(pady=5)
    tk.Label(pw_window, text="Confirm Password:").pack(pady=5)
    conf_pw_entry = tk.Entry(pw_window, width=30, show="*")
    conf_pw_entry.pack(pady=5)
    tk.Button(pw_window, text="Set Password", command=save_manual_password).pack(pady=10)
    tk.Button(pw_window, text="Generate Password & Email", command=generate_and_send).pack(pady=5)
    error_label = tk.Label(pw_window, text="", fg="red")
    error_label.pack()

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

# ----------------- Camera Functions -----------------
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
        import winreg
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
            if os.path.exists(log_file):
                with open(log_file, "r") as log:
                    text_widget.insert(tk.END, log.read())
            else:
                text_widget.insert(tk.END, "No logs found.")
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
    pw_entry = tk.Entry(pw_window, show="*")
    pw_entry.pack(pady=5)
    tk.Button(pw_window, text="OK", command=check_password_and_open).pack(pady=10)
    error_label = tk.Label(pw_window, text="", fg="red")
    error_label.pack()

# ----------------- Face Recognition -----------------
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
face_dir = "faces"
if not os.path.exists(face_dir):
    os.makedirs(face_dir)
recognizer = cv2.face.LBPHFaceRecognizer_create()

def enroll_face():
    user_name = "user"
    user_path = os.path.join(face_dir, user_name)
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    cam = cv2.VideoCapture(0)
    count = 0
    messagebox.showinfo("Info", "Press 'q' to exit preview at any time.")
    while True:
        ret, frame = cam.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray,1.3,5)
        for (x,y,w,h) in faces:
            face_img = gray[y:y+h, x:x+w]
            cv2.imwrite(os.path.join(user_path, f"{count}.jpg"), face_img)
            count += 1
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
        cv2.imshow("Face Enrollment - Press q to exit", frame)
        if cv2.waitKey(1) & 0xFF==ord('q') or count>=20:
            break
    cam.release()
    cv2.destroyAllWindows()
    train_faces()
    messagebox.showinfo("Success", "Face enrolled successfully!")

def train_faces():
    faces = []
    labels = []
    user_name = "user"
    user_path = os.path.join(face_dir,user_name)
    for img_name in os.listdir(user_path):
        img_path = os.path.join(user_path,img_name)
        gray = cv2.imread(img_path,cv2.IMREAD_GRAYSCALE)
        faces.append(gray)
        labels.append(0)
    recognizer.train(faces,np.array(labels))
    recognizer.save("face_model.yml")

def unlock_with_face(action):
    if not os.path.exists("face_model.yml"):
        messagebox.showerror("Error","No face enrolled!")
        return
    recognizer.read("face_model.yml")
    cam = cv2.VideoCapture(0)
    recognized=False
    messagebox.showinfo("Face Unlock","Look at the camera. Press 'q' to quit.")
    while True:
        ret, frame = cam.read()
        if not ret:
            continue
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        faces=face_cascade.detectMultiScale(gray,1.3,5)
        for (x,y,w,h) in faces:
            face_img=gray[y:y+h, x:x+w]
            label, conf = recognizer.predict(face_img)
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            cv2.putText(frame,f"{conf:.0f}",(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,255,0),2)
            if conf<80:
                recognized=True
                break
        cv2.imshow("Face Unlock",frame)
        if recognized or cv2.waitKey(1) & 0xFF==ord('q'):
            break
    cam.release()
    cv2.destroyAllWindows()
    if recognized:
        action()
    else:
        messagebox.showwarning("Failed","Face not recognized!")

# ----------------- Project Info HTML -----------------
def project_info_html():
    html_content = """
    <html>
    <head>
        <title>Project Information</title>
        <style>
            body { font-family: Arial; background:#f5f5f5; }
            .container { max-width:700px;margin:50px auto;background:#fff;padding:20px;box-shadow:0 0 10px rgba(0,0,0,0.1);}
            h2{text-align:center;}
            table{width:100%;border-collapse:collapse;margin-top:20px;}
            th,td{padding:10px;border:1px solid #ccc;text-align:left;}
            th{background:#f0f0f0;}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Project Information</h2>
            <table>
                <tr><th>Project Name</th><td>Web Cam Security from Spyware</td></tr>
                <tr><th>Project Description</th><td>Implementing Physical Security Policy on Web Cam in Devices to Prevent Spyware</td></tr>
                <tr><th>Project Start Date</th><td>--</td></tr>
                <tr><th>Project End Date</th><td>10-October-2025</td></tr>
                <tr><th>Project Status</th><td>Completed</td></tr>
            </table>
            <h3>Developer Details</h3>
            <table>
                <tr><td>23WH1A1238</td><td>MARYAM FATIMA</td></tr>
                <tr><td>23WH1A1244</td><td>AYESHA SULTANA</td></tr>
                <tr><td>23WH1A1253</td><td>NISHAT UNNISA</td></tr>
                <tr><td>23WH1A1206</td><td>R SRISTI</td></tr>
            </table>
        </div>
    </body>
    </html>
    """
    temp_file=os.path.join(os.getcwd(),"project_info.html")
    with open(temp_file,"w") as f:
        f.write(html_content)
    webbrowser.open(f"file:///{temp_file}")

# ----------------- Tkinter UI -----------------
root = tk.Tk()
root.title("Web Cam Security")
root.state('zoomed')  # maximize window

# Background colors for glow
bg_colors = ["#0d0d0d","#1a0000","#330000","#0d0d0d"]
color_index=0
def pulse_bg():
    global color_index
    root.configure(bg=bg_colors[color_index])
    color_index=(color_index+1)%len(bg_colors)
    root.after(300,pulse_bg)
pulse_bg()

# Title
tk.Label(root,text="WebCam Spyware Security",font=("Courier",36,"bold"),fg="#ff1a1a",bg="#0d0d0d").pack(pady=20)

# Project Info button
tk.Button(root,text="Project Info",command=project_info_html,bg="#990000",fg="white",font=("Helvetica",14,"bold")).pack(pady=10)

# Webcam icon
icon_url="https://tse4.mm.bing.net/th/id/OIP.d8wWm-r9PgjFNrZvdZ0b0gHaG2?pid=Api&P=0&h=180"
try:
    response=requests.get(icon_url)
    img=Image.open(io.BytesIO(response.content)).resize((150,150))
    photo=ImageTk.PhotoImage(img)
    tk.Label(root,image=photo,bg="#0d0d0d").pack(pady=10)
except: pass

# Glow Button Creator
def create_glow_button(master,text,command,bg,fg="white"):
    btn=tk.Button(master,text=text,font=("Helvetica",14,"bold"),bg=bg,fg=fg,command=command,relief="raised",bd=4)
    def on_enter(e): btn.config(bg="#ff3333",fg="#000000",relief="groove",bd=6)
    def on_leave(e): btn.config(bg=bg,fg=fg,relief="raised",bd=4)
    btn.bind("<Enter>",on_enter)
    btn.bind("<Leave>",on_leave)
    return btn

# ----------------- Buttons Layout -----------------
frame1 = tk.Frame(root,bg="#0d0d0d")
frame1.pack(pady=20)
create_glow_button(frame1,"Enable Camera (Password)",lambda: require_password(enable_camera),"#ff1a1a").grid(row=0,column=0,padx=50,pady=10)
create_glow_button(frame1,"Disable Camera (Face/Password)",lambda: unlock_with_face(disable_camera),"#ff6666").grid(row=0,column=1,padx=50,pady=10)

frame2 = tk.Frame(root,bg="#0d0d0d")
frame2.pack(pady=10)
create_glow_button(frame2,"Enroll Face",enroll_face,"#ff6666").grid(row=0,column=0,padx=50,pady=10)
create_glow_button(frame2,"Set Password",set_password,"#660000").grid(row=0,column=1,padx=50,pady=10)

frame3 = tk.Frame(root,bg="#0d0d0d")
frame3.pack(pady=10)
create_glow_button(frame3,"View Logs",view_logs,"#660000").grid(row=0,column=0,padx=50,pady=10)
create_glow_button(frame3,"Check Status",check_status,"#660000").grid(row=0,column=1,padx=50,pady=10)

root.mainloop()

