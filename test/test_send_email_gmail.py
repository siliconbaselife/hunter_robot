import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email account credentials
email_user = 'db24cc@gmail.com'
email_password = 'hmif etkk vgav yjme'

# List of recipients
to_emails = ['db24@outlook.com']

# Email content
subject = 'Test Email from Python'
body = 'This is a test email sent from Python using Gmail!'

# Set up the MIME
msg = MIMEMultipart()
msg['From'] = email_user
msg['To'] = ', '.join(to_emails)
msg['Subject'] = subject

msg.attach(MIMEText(body, 'plain'))

# Connect to the Gmail SMTP server using SMTP_SSL
server = smtplib.SMTP_SSL('smtp.gmail.com', 465)

try:
    # Log in to the server
    server.login(email_user, email_password)

    # Send the email
    text = msg.as_string()
    server.sendmail(email_user, to_emails, text)

    print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
finally:
    # Quit the server
    server.quit()