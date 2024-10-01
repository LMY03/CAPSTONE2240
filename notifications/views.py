from django.shortcuts import render
import os
import requests
import json
from decouple import config
from services.google_services import Create_Service

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email_sendgrid (paramData):

    url = "https://api.sendgrid.com/v3/mail/send"
    
    headers = {
        "Authorization": f"Bearer {config('SEND_GRID_SECRET')}",  # Replace with your API key
        "Content-Type": "application/json"
    }

    data = paramData
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        # Check if the request was successful
        if response.status_code == 202:
            print("Email sent successfully!")
        else:
            print(f"Failed to send email. Status code: {response.status_code}")
            print(f"Response: {response.text}")
        return response
    except Exception as e:
        return print(f"An error occurred: {str(e)}")
        


def comment_notif_tsg (to_email, data):
    recipients = [{"email": email} for email in to_email]
    data = {
        "from": {
            "email": config('EMAIL_HOST_USER')
        },
        "personalizations": [
            {
                "to": recipients,
                "dynamic_template_data": {
                    "vm_template_name": data['vm_template_name'],
                    "use_case": data['use_case'],
                    "vm_count": data['vm_count'],
                    "faculty_name" : data['faculty_name'],
                    "receipt": True,
                }
            }
        ],
        "template_id": "d-4ce501347a4647d6a09acf7f6baa2b8c"  
    }

    return  send_email_sendgrid(data)

def comment_notif_faculty(to_email, data, *faculty):
    print('inside comment_notif_faculty')
    faculty = faculty if faculty else ('default_value',)
    faculty_name = data.get('faculty_name', '')
    email_data = {
        "from": {
            "email": config('EMAIL_HOST_USER')
        },
        "personalizations": [
            {
                "to": [],  # Placeholder to be populated
                "dynamic_template_data": {
                    "request_id": data['request_entry_id'],
                    "comment": data['comment'],
                    "faculty_name": faculty_name,
                    "receipt": True,
                }
            }
        ]
    }

    if 'faculty' in faculty:
        email_data['personalizations'][0]['to'] = [{"email": f"{to_email}"}]  
        email_data["template_id"] = "d-f532416d64ea429a81671879794c0958"  
    elif 'admin' in faculty:
        # Assuming `to_email` is a list of emails for admins
        recipients = [{"email": email} for email in to_email]
        email_data['personalizations'][0]['to'] = recipients
        email_data["template_id"] = "d-e3593d8aabbc435ba143717a33ce1485"  
    else:
        email_data['personalizations'][0]['to'] = [{"email": f"{to_email}"}]
        email_data["template_id"] = "d-0aabc8df6cf444c09777b1a3e485bf9d"  
    
    return send_email_sendgrid(email_data)

def testVM_notif_faculty(to_email, data):
    email_data = {
        "from": {
            "email": config('EMAIL_HOST_USER')
        },
        "personalizations": [
            {
                "to": [{
                    "email" : f"{to_email}"
                }],
                "dynamic_template_data": {
                    "faculty_name": data['faculty_name'],
                    "request_entry_id": data['id'],
                    "receipt": True,
                }
            }
        ],
        "template_id": "d-a81d10b1b37741808e5ffada2ec1998e"  
    }

    return send_email_sendgrid(email_data)

def reject_notif_faculty (to_email, data):
    email_data = {
        "from": {
            "email": config('EMAIL_HOST_USER')
        },
        "personalizations": [
            {
                "to": [{
                    "email" : f"{to_email}"
                }],
                "dynamic_template_data": {
                    "faculty_name": data['faculty_name'],
                    "request_entry_id": data['id'],
                    "receipt": True,
                }
            }
        ],
        "template_id": "d-e68d6433360241df9b5760dc6b0915ea"  
    }

    return send_email_sendgrid(email_data)


def accept_notif_tsg (to_email, data):
    email_data = {
        "from": {
            "email": config('EMAIL_HOST_USER')
        },
        "personalizations": [
            {
                "to": [{
                    "email" : f"{to_email}"
                }],
                "dynamic_template_data": {
                    "faculty_name": data['faculty_name'],
                    "request_entry_id": data['id'],
                    "use_case" : data['use_case'],
                    "vm_count" : data['vm_count'],
                    "receipt": True,
                }
            }
        ],
        "template_id": "d-049d70ccac974157828e6bfbbe2c8a1a"  
    }

    return send_email_sendgrid(email_data)

def confirm_notif_faculty(to_email, data):
    return send_email_sendgrid(data)


CLIENT_SECRET_FILE = {
    "web": {
        "client_id": config("SECRET_CLIENT_ID"),
        "project_id": "capstone-2240",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": config("SECRET_CLIENT_SECRET"),
        "redirect_uris": [
            "http://localhost:8000/social-auth/complete/google-oauth2/"
        ],
        "javascript_origins": [
            "http://localhost:8000",
            "http://127.0.0.1:8000"
        ]
    }
}
API_NAME = 'gmail'
API_VERSION = 'v1'
SCOPES = ['https://mail.google.com/']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

# emailMsg = 'You won $100,000'
# mimeMessage = MIMEMultipart()
# mimeMessage['to'] = '<Receipient>@gmail.com'
# mimeMessage['subject'] = 'You won'
# mimeMessage.attach(MIMEText(emailMsg, 'plain'))
# raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()

# message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
# print(message)