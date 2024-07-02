from typing import Any
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from ticketing.models import RequestEntry, Comment, RequestUseCase, VMTemplates, UserProfile, PortRules
import json
from django.forms.models import model_to_dict
from proxmox.models import VirtualMachines
from guacamole.models import GuacamoleConnection

# Create your views here.
def home_filter_view (request):
    status = request.GET.get('status')
    request_list = RequestEntry.objects.filter(status = status)
    return render (request, 'users/tsg_requests.html', {'request_list': request_list, 'status': status})

def get_student_vm ():
    # Get the list of VM IDs from VMTemplates
    template_vm_ids = VMTemplates.objects.values_list('vm_id', flat=True)
    # Filter VirtualMachines to exclude those in VMTemplates and with status 'DELETED'
    return list(VirtualMachines.objects.exclude(id__in=template_vm_ids).exclude(status='DELETED').order_by('id').values())

@login_required
def student_home(request):
    return render(request, 'users/student_home.html', {'data': get_student_vm()})

@login_required
def faculty_home(request):
    return render(request, 'users/faculty_home.html', {'data': get_student_vm()})
    

@login_required
def tsg_home(request):
    return render(request, 'users/tsg_home.html')


@login_required
def vm_details(request, vm_id):
    vm_data = VirtualMachines.objects.get(id=vm_id)
    guacamole_connection = GuacamoleConnection.objects.get(vm=vm_data)
    print("guacamole_connection")
    print(guacamole_connection)
    context = {
        'vm_data': vm_data,
        'data' : get_student_vm(),
        'guacamole_connection' : guacamole_connection
    }

    return render(request, 'users/student_vm_details.html', context)

def tsg_requests (request):
    datas = RequestEntry.objects.select_related("requester", "template").values(
            "status",
            "requester__first_name",
            "requester__last_name",
            "cores",
            "ram",
            "has_internet",
            "id",
            "template__vm_name"
        )
    # context['request_list'] = datas
    context = {'request_list': datas}
    print (context)
    return render (request, 'users/tsg_requests.html', context= context)

def request_details (request, request_id):
    context = {}
    pk = request_id
    request_entry = get_object_or_404(RequestEntry, pk=pk)

    request_entry_details = RequestEntry.objects.select_related("requester", "template").values(
        "id",
        "status",
        "requester__first_name",
        "requester__last_name",
        "cores",
        "ram",
        #"storage",
        "has_internet",
        "id",
        "template__vm_name",
        #"use_case",
        "date_needed",
        'expiration_date',
        "other_config",
        "template__storage"
    ).get(pk=pk)


    request_use_cases = RequestUseCase.objects.filter(request_id = request_entry_details.get('id'))

    for request_use_case in request_use_cases:
        if request_use_case.request_use_case == 'RESEARCH':
            request_entry_details['use_case'] = 'Research'
        elif request_use_case.request_use_case == 'THESIS':
            request_entry_details['use_case'] = 'Thesis'
        elif request_use_case.request_use_case == 'TEST':
            request_entry_details['use_case'] = 'Test'
        else:
            request_entry_details['use_case'] = 'Class Course'

    request_entry_details['storage'] = request_entry_details.get('template__storage')


    comments = Comment.objects.filter(request_entry=request_entry).order_by('-date_time')
    context['request_entry'] = {
        'details': request_entry_details,
        'comments' : comments,
        'request_use_cases': request_use_cases,
    }
    print (request_use_cases)
    return render (request, 'users/tsg_request_details.html', context = context)

def faculty_vm_details (request, vm_id):
    context ={
        'vm_id' : vm_id,
    }
    return render (request, 'users/faculty_vm_details.html', context = context)

def faculty_request_list(request):
    user = get_object_or_404(User, username=request.user.username)
    request_entries = RequestEntry.objects.filter(requester=user)

    for request_entry in request_entries:
        category = 'Unknown'  
        request_use_case = RequestUseCase.objects.filter(request_id=request_entry).first()
        
        if request_use_case:
            if request_use_case.request_use_case == 'RESEARCH':
                category = 'Research'
            elif request_use_case.request_use_case == 'TEST':
                category = 'Test'
            elif request_use_case.request_use_case == 'THESIS':
                category = 'Thesis'
            else:
                category = 'Class Course'
        
        request_entry.category = category

    context = {
        'request_entries': request_entries
    }

    return render(request, 'users/faculty_request_list.html', context)

def edit_request(request, request_id):
    request_entry = get_object_or_404(RequestEntry, pk = request_id)
    request_use_cases = RequestUseCase.objects.filter(request_id = request_id)
    portRules = PortRules.objects.filter(request_id = request_id)
    context = {
        'Sections': [],
        'use_case': None 
    }
    for use_case in request_use_cases:
        print (use_case)
        if use_case.request_use_case == 'RESEARCH':
            context['use_case'] = 'RESEARCH'
        elif use_case.request_use_case == 'THESIS':
            context['use_case'] = 'THESIS'
        elif use_case.request_use_case == 'TEST':
            context['use_case'] = 'TEST'
        else:
            context['use_case'] = 'CLASS_COURSE'
        
        # Append to Sections based on conditions
        if context['use_case'] == 'CLASS_COURSE':
            context['Sections'].append({
                'request_use_case' : use_case.request_use_case,
                'vm_count' : use_case.vm_count,
                'id': use_case.id
            })
        else:
            context['vm_count'] = use_case.vm_count

    vmtemplate_list = VMTemplates.objects.all().values_list('id', 'vm_name')
    context['vmtemplate_list'] = list(vmtemplate_list)
    context['request_entry'] = request_entry

    if portRules.exists():
        port_rules_list = list(portRules.values())
        context['port_rules'] = portRules
        context['port_rules_js'] = json.dumps(port_rules_list)

    comments = Comment.objects.filter(request_entry=request_entry).select_related("user").values(
            "comment",
            "user__first_name",
            "user__last_name",
            "date_time",
        ).order_by('-date_time')

    if comments.exists():
        context['comments'] = comments

    print(context)
    return render(request, 'users/faculty_edit_request.html', context)


def login_view (request):
    data = request.POST
    username = data.get("username")
    password = data.get("password")

    user = authenticate(request, username=username, password=password)
        
    if user is not None:
        # Log in the user
        login(request, user)
        user_profile = request.user.userprofile
        if user_profile.user_type == 'student':
            return redirect('users:student_home')
        elif user_profile.user_type == 'faculty':
            return redirect('users:faculty_home')
        elif user_profile.user_type == 'admin':
            return redirect('users:tsg_home')
    else:
        # Handle invalid login
        return render(request, 'login.html', {'error': 'Invalid username or password'})
    
def faculty_test_vm (request, request_id):
    vm = VirtualMachines.objects.filter(request_id=request_id, vm_name__startswith='test')
    context = {}
    request_entry = get_object_or_404(RequestEntry, pk = request_id)
    context['vm_data'] = vm.first()
    context ['comments'] = Comment.objects.filter(request_entry=request_entry).select_related("user").values(
            "comment",
            "user__first_name",
            "user__last_name",
            "date_time",
        ).order_by('-date_time')
    context['request_entry'] ={
        'id' : request_id
    }
    return render(request, 'users/faculty_test_vm.html', context)
