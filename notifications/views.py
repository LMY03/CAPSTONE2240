from django.shortcuts import render
import os, requests, json, pybars
from decouple import config
from .google_services import Create_Service

from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request

# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

CLIENT_SECRET_FILE = './credentials.json'
API_NAME = 'gmail'
API_VERSION = 'v1'
SCOPES = ['https://mail.google.com/']

def new_request_notif_tsg (to_email, data):
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    mimeMessage = MIMEMultipart()
    mimeMessage["to"] = ", ".join(to_email)
    mimeMessage['subject'] = 'New request ticket for VM provisioning'
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, 'templates', 'notifications', 'add_comment_email_tsg.hbs')
    print (template_path)
    with open(template_path, 'r') as f:
            source = f.read()

    data = {
            "vm_template_name": data['vm_template_name'],
            "use_case": data['use_case'],
            "vm_count": data['vm_count'],
            "faculty_name" : data['faculty_name']
    }

    compiler = pybars.Compiler()
    template = compiler.compile(source)
    html_body = template(data)
    mimeMessage.attach(MIMEText(html_body, 'html'))
    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()
    
    message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()

    return  message

def comment_notif_faculty(to_email, data, *faculty):
    print('inside comment_notif_faculty')
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    faculty = faculty if faculty else ('default_value',)
    faculty_name = data.get('faculty_name', '')
    email_data = {
        "request_id": data['request_entry_id'],
        "comment": data['comment'],
        "faculty_name": faculty_name,
        "receipt": True,
    }
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mimeMessage = MIMEMultipart()
    if 'faculty' in faculty: 
        mimeMessage['to'] = f'{to_email}'
        #     email_data["template_id"] = "d-f532416d64ea429a81671879794c0958"
        mimeMessage['subject'] = 'The faculty has replied to your comment'
        template_path = os.path.join(base_dir, 'templates', 'notifications', 'replied_comment_faculty.hbs')
        with open(template_path, 'r') as f:
            source = f.read()
    elif 'admin' in faculty:
        mimeMessage['to'] = ', '.join(to_email)
        mimeMessage["subject"] = 'Faculty has added a new comment in their request ticket'
        #     email_data["template_id"] = "d-e3593d8aabbc435ba143717a33ce1485"
        template_path = os.path.join(base_dir, 'templates', 'notifications', 'add_comment_without_assigned_tsg.hbs')
        with open(template_path, 'r') as f:
            source = f.read()
    else:
        mimeMessage['to'] = f'{to_email}'
        mimeMessage["subject"] = 'An Admin has made some comments about your request'
        #     email_data["template_id"] = "d-0aabc8df6cf444c09777b1a3e485bf9d"
        template_path = os.path.join(base_dir, 'templates', 'notifications', 'add_comment_email.hbs')
        with open(template_path, 'r') as f:
            source = f.read()

    compiler = pybars.Compiler()
    template = compiler.compile(source)
    html_body = template(email_data)
    mimeMessage.attach(MIMEText(html_body, 'html'))
    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()
    
    message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
    print(message)
    
    return message

def testVM_notif_faculty(to_email, data):
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    mimeMessage = MIMEMultipart()
    mimeMessage["to"] = f'{to_email}'
    mimeMessage['subject'] = 'A test virtual machine has been created'
    email_data = {
            "faculty_name": data['faculty_name'],
            "request_entry_id": data['id'],
    }
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, 'templates', 'notifications', 'test_vm_notif_faculty.hbs')
    with open(template_path, 'r') as f:
            source = f.read()
    
    compiler = pybars.Compiler()
    template = compiler.compile(source)
    html_body = template(email_data)
    mimeMessage.attach(MIMEText(html_body, 'html'))
    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()
    
    message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
    print(message)
    
    return message

def reject_notif_faculty (to_email, data):
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    mimeMessage = MIMEMultipart()
    mimeMessage["to"] = f'{to_email}'
    mimeMessage['subject'] = 'Your request has been rejected by the admin'
    email_data = {
            "faculty_name": data['faculty_name'],
            "request_entry_id": data['id'],
            "receipt": True,
    }
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, 'templates', 'notifications', 'reject_ticket_faculty.hbs')
    with open(template_path, 'r') as f:
        source = f.read()
    compiler = pybars.Compiler()
    template = compiler.compile(source)
    html_body = template(email_data)
    mimeMessage.attach(MIMEText(html_body, 'html'))
    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()
    
    message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
    print(message)
    
    return message

def accept_notif_tsg (to_email, data):
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    mimeMessage = MIMEMultipart()
    mimeMessage["to"] = f'{to_email}'
    mimeMessage['subject'] = 'The test virtual machine has been accepted'
    email_data = {
        "faculty_name": data['faculty_name'],
        "request_entry_id": data['id'],
        "use_case" : data['use_case'],
        "vm_count" : data['vm_count'],
    }
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, 'templates', 'notifications', 'faculty_accept_test_vm_tsg.hbs')
    with open(template_path, 'r') as f:
        source = f.read()
    compiler = pybars.Compiler()
    template = compiler.compile(source)
    html_body = template(email_data)
    mimeMessage.attach(MIMEText(html_body, 'html'))
    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()
    
    message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
    print(message)
    
    return message

def confirm_notif_faculty(to_email):
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    mimeMessage = MIMEMultipart()
    mimeMessage["to"] = f'{to_email}'
    mimeMessage['subject'] = 'You have have a newly created account in Proxmon.'
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, 'templates', 'notifications', 'confirm_notif_faculty.hbs')
    with open(template_path, 'r') as f:
        source = f.read()
    compiler = pybars.Compiler()
    template = compiler.compile(source)
    html_body = template()
    mimeMessage.attach(MIMEText(html_body, 'html'))
    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()
    
    message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
    print(message)
    
    return message


def added_user_notif (to_email, username, password):
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    mimeMessage = MIMEMultipart()
    mimeMessage["to"] = f'{to_email}'
    mimeMessage['subject'] = 'You have have a newly created account in Proxmon.'
    email_data = {
        "username": username,
        "password": password,
    }
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, 'templates', 'notifications', 'added_users_email.hbs')
    with open(template_path, 'r') as f:
        source = f.read()
    compiler = pybars.Compiler()
    template = compiler.compile(source)
    html_body = template(email_data)
    mimeMessage.attach(MIMEText(html_body, 'html'))
    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()
    
    message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
    print(message)
    
    return message

