import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL_HOST_USER", "your_email@gmail.com")
APP_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "your_app_password")
FROM_NAME = os.getenv("DEFAULT_FROM_EMAIL_NAME", "Fraud Detection System")

def send_otp_email(to_email, otp):
    subject = "⚠️ Fraud Detected - OTP Verification"
    
    body = f"""
    Fraudulent activity detected!

    Your OTP is: {otp}

    Please verify to complete your transaction.
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{EMAIL}>"
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("✅ Email sent successfully")

    except Exception as e:
        print("❌ Email error:", e)