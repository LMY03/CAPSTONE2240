from django.shortcuts import render

import os
from decouple import config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_email_sendgrid (to_email, subject, html_content):
    message = Mail(
        from_email='patrick_bennett_ong@dlsu.edu.ph',
        to_emails= to_email,
        subject= subject,
        html_content= html_content)
    try:
        sg = SendGridAPIClient(config('SEND_GRID_SECRET'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
