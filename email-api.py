import os
import smtplib
from email.message import EmailMessage


EMAIL_ADDRESS = ''
EMAIL_PASSWOWORD = ''

msg = EmailMessage()
msg['Subject'] = ''
msg['From'] = EMAIL_ADDRESS
msg['To'] = ''
msg.set_content('')

with smtplib.SMTP_SSL(smtp.gmail.com, 465) as smtp:
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWOWORD)

    smtp.send_message(msg)