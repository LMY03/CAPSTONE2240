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
    data = {
        "from": {
            "email": "patrick_bennett_ong@dlsu.edu.ph"
        },
        "personalizations": [
            {
                "to": [
                    {
                        "email": f"{to_email}"
                    }
                ],
                "dynamic_template_data": {
                    "request_id": data.request_entry_id,
                    "comment": data.comment,
                    "receipt": True,
                }
            }
        ],
        "template_id": "d-4ce501347a4647d6a09acf7f6baa2b8c"  # Replace with your SendGrid dynamic template ID
    }

    return  send_email_sendgrid(data)

def comment_notif_faculty (to_email, data):
    recipients = [{"email": email} for email in to_email]
    data = {
        "from": {
            "email": "patrick_bennett_ong@dlsu.edu.ph"
        },
        "personalizations": [
            {
                "to": recipients,
                "dynamic_template_data": {
                    "request_id": data.request_entry_id,
                    "comment": data.comment,
                    "receipt": True,
                }
            }
        ],
        "template_id": "d-0aabc8df6cf444c09777b1a3e485bf9d"  # Replace with your SendGrid dynamic template ID
    }

    return  send_email_sendgrid(data)