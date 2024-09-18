from django.shortcuts import render
import os
import requests
import json
from decouple import config

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


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
            "email": "patrick_bennett_ong@dlsu.edu.ph"
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
        "template_id": "d-4ce501347a4647d6a09acf7f6baa2b8c"  # Replace with your SendGrid dynamic template ID
    }

    return  send_email_sendgrid(data)

def comment_notif_faculty(to_email, data, *faculty):
    print('inside comment_notif_faculty')
    faculty = faculty if faculty else ('default_value',)
    faculty_name = data.get('faculty_name', '')
    email_data = {
        "from": {
            "email": "patrick_bennett_ong@dlsu.edu.ph"
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
        # Default case
        email_data['personalizations'][0]['to'] = [{"email": f"{to_email}"}]
        email_data["template_id"] = "d-0aabc8df6cf444c09777b1a3e485bf9d"  
    
    return send_email_sendgrid(email_data)
