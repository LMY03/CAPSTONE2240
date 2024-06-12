from typing import Any
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from ticketing.models import RequestEntry, Comment, RequestUseCase, GroupList, VMTemplates, UserProfile
from django.shortcuts import redirect
import json
from django.forms.models import model_to_dict

# Create your views here.
def home_filter_view (request):
    status = request.GET.get('status')
    request_list = RequestEntry.objects.filter(status = status)
    return render (request, 'users/tsg_requests.html', {'request_list': request_list, 'status': status})

@login_required
def student_home(request):
    return render(request, 'users/student_home.html')

@login_required
def faculty_home(request):
    return render(request, 'users/faculty_home.html')
    

@login_required
def tsg_home(request):
    return render(request, 'users/tsg_home.html')


@login_required
def vm_details(request, vm_id):
    print(f"This is the VM ID: {vm_id}")

    vm_data = {
        'vm_id' : vm_id,
    }
    return render (request, 'users/student_vm_details.html', context= vm_data)

def tsg_requests (request):
    context = {}
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
    context['request_list'] = datas
    return render (request, 'users/tsg_requests.html', context= context)

def request_details (request, request_id):
    context = {}
    pk = request_id
        # Fetch the RequestEntry object
    request_entry = get_object_or_404(RequestEntry, pk=pk)

    # Get the use case details as well and group them
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
            "vm_count",
            "template__storage"
    ).get(pk=pk)

    if request_entry_details.get('storage') == 0.0:
            request_entry_details['storage'] = request_entry_details.get('template__storage')

    # Fetch the comments related to the request_entry
    comments = Comment.objects.filter(request_entry=request_entry).order_by('-date_time')
    context['request_entry'] = {
        'details': request_entry_details,
        'comments' : comments
    }

    return render (request, 'users/tsg_request_details.html', context = context)

def faculty_vm_details (request, vm_id):
     context ={
          'vm_id' : vm_id,
     }
     return render (request, 'users/faculty_vm_details.html', context = context)

def faculty_request_list(request):
     return render (request, 'users/faculty_request_list.html')