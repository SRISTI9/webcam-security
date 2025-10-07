🛡️ WebCam Spyware Security

WebCam Spyware Security is a Python desktop application that protects your webcam from unauthorized access, logs webcam activity, secures access with passwords, and even supports face recognition for unlocking sensitive actions. You can also generate and email passwords safely.

🚀 Features

🔒 Enable/Disable Webcam: Control your webcam access on Windows.

👤 Face Recognition Unlock: Disable the webcam using face authentication.

🔑 Password Management: Set custom or randomly generated passwords.

📧 Email Passwords: Send generated passwords securely via email.

📜 Activity Logs: All actions are logged to a file (camera_log.txt).

🖥️ Check Webcam Status: Instantly verify if the webcam is enabled or disabled.

🎨 User-Friendly GUI: Built with Tkinter, with interactive glow buttons.

🌐 Project Info Page: View detailed project and developer info in a separate HTML page.

🛠️ Tech Stack

Python 3.x – Programming language

Tkinter – GUI framework

OpenCV – Face detection & recognition

Pillow (PIL) – Image processing for icons

SMTP/SSL – Sending emails securely

Requests – Fetch images from URLs

Windows Registry – Webcam access control (Admin privileges required)

⚡ Installation
git clone <repository_url>
cd webcam-security
pip install opencv-python opencv-contrib-python pillow requests


Note: opencv-contrib-python is required for the LBPH face recognizer.

🖱️ Usage

Run the application:

python main.py


Use the GUI buttons:

Set Password – Set a custom password or generate & email a secure password.

Enable Camera (Password) – Enable the webcam using a password.

Disable Camera (Face/Password) – Disable the webcam using face recognition or password.

Enroll Face – Capture and train your face for face unlock.

View Logs – Access action logs (password-protected).

Check Status – See if the webcam is currently enabled or disabled.

Project Info – Open a separate HTML page with project details and developer info.

🔐 Security Notes

Webcam control works via Windows Registry edits – Admin rights are required.

Passwords are stored securely in memory during the session.

All actions are logged locally in camera_log.txt.

Face recognition allows secure access without typing the password.

Always use strong passwords and keep your email app password secure.
