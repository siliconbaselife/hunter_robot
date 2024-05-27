import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Fetch credentials from environment variables
email_user = 'silicon_based_life@163.com'
email_password = 'KUKWNNYRLPCRCDMN'
to_emails = ['db24@outlook.com', 'lishundong2009@163.com']

subject = 'Test Email to Multiple Recipients Using SMTP_SSL'
body = 'This is a test email sent to multiple recipients from Python using 163.com with SSL!'

msg = MIMEMultipart()
msg['From'] = email_user
msg['To'] = ', '.join(to_emails)
msg['Subject'] = subject

msg.attach(MIMEText(body, 'plain'))

all_recipients = to_emails

try:
    server = smtplib.SMTP_SSL('smtp.163.com', 465)
    server.login(email_user, email_password)
    text = msg.as_string()
    server.sendmail(email_user, all_recipients, text)
    print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
finally:
    server.quit()
