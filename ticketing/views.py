from typing import Any
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.core.mail import send_mail
from decouple import config
import json, datetime

from.tasks import delete_request as delete_request_process
from proxmox.tasks import create_test_vm, processing_ticket

from guacamole import guacamole
from proxmox import views, proxmox
from pfsense.views import add_port_forward_rules, delete_port_forward_rules

from .models import RequestEntry, Comment, RequestUseCase, PortRules, UserProfile, RequestEntryAudit, VMTemplates, IssueTicket, IssueFile, IssueComment, IssueCommentFile
from proxmox.models import VirtualMachines, Nodes
from guacamole.models import GuacamoleConnection, GuacamoleUser
from pfsense.models import DestinationPorts
from notifications.views import comment_notif_faculty, comment_notif_tsg, testVM_notif_faculty, reject_notif_faculty, accept_notif_tsg
from .forms import IssueTicketForm, IssueCommentForm

from CAPSTONE2240.utils import download_files

# Create your views here.

@login_required
def request_list(request):
    user_role = get_object_or_404(UserProfile, user=request.user).user_type
    if user_role == 'faculty' : return faculty_request_list(request)
    elif user_role == 'admin' : return tsg_requests_list(request)
    else : return redirect('/')
    
def faculty_request_list(request):
    user = get_object_or_404(User, username=request.user.username)
    request_entries = RequestEntry.objects.filter(requester=user).order_by('-id')

    return render(request, 'ticketing/faculty_request_list.html', { 'request_entries' : request_entries })

def tsg_requests_list(request):
    return render(request, 'ticketing/tsg_request_list.html', { 'request_entries' : RequestEntry.objects.all().order_by('-id') })

@login_required
def request_details(request, request_id):
    user_role = get_object_or_404(UserProfile, user=request.user).user_type
    if user_role == 'faculty' : return faculty_request_details(request, request_id)
    elif user_role == 'admin' : return tsg_request_details(request, request_id)
    else : return redirect('/')

def faculty_request_details(request, request_id):
    request_entry = get_object_or_404(RequestEntry, pk=request_id)

    request_use_cases = RequestUseCase.objects.filter(request=request_entry)

    for request_use_case in request_use_cases:
        if request_use_case.request_use_case == 'RESEARCH' : request_entry.use_case = 'Research'
        elif request_use_case.request_use_case == 'THESIS' : request_entry.use_case = 'Thesis'
        elif request_use_case.request_use_case == 'TEST' : request_entry.use_case = 'Test'
        else: request_entry.use_case = 'Class Course'

    if request_entry.status == RequestEntry.Status.PROCESSING : request_entry.vm_id = get_object_or_404(VirtualMachines, request=request_entry).id

    comments = Comment.objects.filter(request_entry=request_entry).order_by('date_time')

    port_rules = PortRules.objects.filter(request_id=request_id)
    context = {
        'request_entry': request_entry,
        'comments' : comments,
        'request_use_cases': request_use_cases,
        'port_rules' : port_rules,
        'issue_form' : IssueTicketForm(initial={'request_entry': request_id})
    }
    request_entry.storage = request_entry.template.storage

    if request_entry.is_ongoing:
        context['destination_ports'] = DestinationPorts.objects.filter(port_rule__in=port_rules)
        context['system_accounts'] = VirtualMachines.objects.filter(request=request_entry)

    return render (request, 'ticketing/faculty_request_details.html', context=context)

def tsg_request_details(request, request_id):
    request_entry = get_object_or_404(RequestEntry, pk=request_id)

    request_use_cases = RequestUseCase.objects.filter(request=request_entry)

    for request_use_case in request_use_cases:
        if request_use_case.request_use_case == 'RESEARCH' : request_entry.use_case = 'Research'
        elif request_use_case.request_use_case == 'THESIS' : request_entry.use_case = 'Thesis'
        elif request_use_case.request_use_case == 'TEST' : request_entry.use_case = 'Test'
        else: request_entry.use_case = 'Class Course'

    if request_entry.is_processing() : request_entry.vm_id = get_object_or_404(VirtualMachines, request=request_entry).id

    comments = Comment.objects.filter(request_entry=request_entry).order_by('date_time')
    vm_counts = 0
    for use_case in request_use_cases:
        vm_counts += use_case.vm_count
    
    total_request_cores = request_entry.cores * vm_counts
    total_request_ram = (request_entry.ram * vm_counts) / 1024
    total_request_storage = request_entry.template.storage * vm_counts

    total_request_details ={
        'total_cores' : total_request_cores,
        'total_ram' : total_request_ram,
        'total_storage' : total_request_storage
    }

    port_rules = PortRules.objects.filter(request_id=request_id)
    context = {
        'request_entry': request_entry,
        'comments' : comments,
        'request_use_cases': request_use_cases,
        'total_request_details' : total_request_details,
        'port_rules' : port_rules,
        'no_vm': request_entry.get_total_no_of_vm()
    }

    if request_entry.is_pending() : context['nodes'] = Nodes.objects.all().values_list('name', flat=True)
    if 'credentials' in request.session : request_entry.has_credentials = True
    request_entry.storage = request_entry.template.storage

    if request_entry.is_ongoing:
        context['destination_ports'] = DestinationPorts.objects.filter(port_rule__in=port_rules)
        context['system_accounts'] = VirtualMachines.objects.filter(request=request_entry)
        
    return render (request, 'ticketing/tsg_request_details.html', context=context)

@login_required
def ticket_list(request):
    user_role = get_object_or_404(UserProfile, user=request.user).user_type
    if user_role == 'faculty' : return faculty_ticket_list(request)
    elif user_role == 'admin' : return tsg_ticket_list(request)
    else : return redirect('/')

def tsg_ticket_list(request):

    issue_tickets = IssueTicket.objects.all().order_by('-id')

    context = {
        'issue_tickets': issue_tickets
    }

    return render(request, 'ticketing/tsg_ticket_list.html', context)

def faculty_ticket_list(request):

    issue_tickets = IssueTicket.objects.filter().order_by('-id')

    context = {
        'issue_tickets': issue_tickets
    }

    return render(request, 'ticketing/faculty_ticket_list.html', context)

@login_required
def ticket_details(request, ticket_id):
    user_role = get_object_or_404(UserProfile, user=request.user).user_type
    if user_role == 'faculty' : return faculty_ticket_details(request, ticket_id)
    elif user_role == 'admin' : return tsg_ticket_details(request, ticket_id)
    else : return redirect('/')

def faculty_ticket_details(request, ticket_id):

    issue_ticket = get_object_or_404(IssueTicket, pk=ticket_id)
    issue_files = IssueFile.objects.filter(ticket=issue_ticket)

    comments = IssueComment.objects.filter(ticket=issue_ticket).order_by('date_time')
    for comment in comments : comment.files = IssueCommentFile.objects.filter(comment=comment)

    context = {
        'issue_ticket': issue_ticket,
        'issue_files': issue_files,
        'comments': comments,
        'issue_comment_form': IssueCommentForm(initial={'ticket': ticket_id}),
    }

    return render(request, 'ticketing/faculty_ticket_details.html', context)

def tsg_ticket_details(request, ticket_id):

    issue_ticket = get_object_or_404(IssueTicket, pk=ticket_id)
    issue_files = IssueFile.objects.filter(ticket=issue_ticket)

    comments = IssueComment.objects.filter(ticket=issue_ticket).order_by('date_time')
    for comment in comments : comment.files = IssueCommentFile.objects.filter(comment=comment)

    context = {
        'issue_ticket': issue_ticket,
        'issue_files': issue_files,
        'comments': comments,
        'issue_comment_form': IssueCommentForm(initial={'ticket': ticket_id}),
    }

    return render(request, 'ticketing/tsg_ticket_details.html', context)

def submit_issue_ticket(request):
    if request.method == 'POST':
        form = IssueTicketForm(request.POST)
        if form.is_valid():
            issue_ticket = form.save(commit=False)
            request_entry_id = form.cleaned_data['request_entry']
            request_entry = get_object_or_404(RequestEntry, pk=request_entry_id)
            issue_ticket.request = request_entry
            issue_ticket.created_by = request.user
            issue_ticket.save()

            files = request.FILES.getlist('files')
            for file in files:
                IssueFile.objects.create(
                    file=file,  # This will save the actual file
                    uploaded_date=timezone.now(),
                    ticket=issue_ticket,
                    uploaded_by=request.user
                )

            return redirect(reverse('ticketing:request_details', args=[request_entry_id]))
        
    return redirect('ticketing:index')

def resolve_issue_ticket(request):
    if request.method == 'POST':
        issue_ticket_id = request.POST.get('issue_ticket_id')
        issue_ticket = get_object_or_404(IssueTicket, pk=issue_ticket_id)
        
        issue_ticket.resolve_ticket()

        return redirect(reverse('ticketing:ticket_details', args=[issue_ticket_id]))
    
    return redirect('ticketing:ticket_list')

def download_issue_files(request, ticket_id):
    file_paths = IssueFile.objects.filter(ticket__pk=ticket_id).values_list('file', flat=True)
    zip_filename = f"ticket_{ticket_id}_files.zip"
    
    return download_files(zip_filename, file_paths)

@login_required
def add_ticket_comment(request, issue_ticket_id):
    if request.method == 'POST':
        print("posted")
        form = IssueCommentForm(request.POST)

        if form.is_valid():
            print("valid")
            issue_comment = form.save(commit=False)
            issue_ticket_id = form.cleaned_data['ticket']
            issue_ticket = get_object_or_404(IssueTicket, pk=issue_ticket_id)
            issue_comment.ticket = issue_ticket
            issue_comment.user = request.user
            issue_comment.save()
            
            files = request.FILES.getlist('files')
            if files:
                for file in files:
                    IssueCommentFile.objects.create(
                        file=file,
                        comment=issue_comment,
                    )
            

            return redirect(reverse('ticketing:ticket_details', args=[issue_ticket_id]))
        
    return redirect('ticketing:index')

def download_issue_comment_files(request, issue_comment_id):
    file_paths = IssueCommentFile.objects.filter(comment__pk=issue_comment_id).values_list('file', flat=True)
    zip_filename = f"ticket_{issue_comment_id}_files.zip"
    
    return download_files(zip_filename, file_paths)

@login_required
def add_comment(request, pk):
    request_entry = get_object_or_404(RequestEntry, pk=pk)
    if request.method == 'POST':
        user = request.user
        user_profile = get_object_or_404(UserProfile, user=user)
        requester_user = request_entry.requester
        new_data = {}
        
        if request_entry.assigned_to is None and user_profile.user_type == 'admin':
            new_data['assigned_to'] = user
        
        comment_text = request.POST.get('comment')
        
        if request_entry.status == RequestEntry.Status.PENDING:
            new_data['status'] = RequestEntry.Status.FOR_REVISION

        if user_profile.user_type == 'admin':
            data = {
                'comment' : comment_text, 
                'request_entry_id' : request_entry.id
            }
            print(requester_user.email, data)
            comment_notif_faculty(requester_user.email, data) # Admin comments to the request ticket
        elif user_profile.user_type == 'faculty':
            data = {
                'comment' : comment_text, 
                'request_entry_id' : request_entry.id, 
                'faculty_name': requester_user.get_full_name()
            }
            if request_entry.assigned_to and request_entry.assigned_to.email: #Checks if there is an assigned TSG
                comment_notif_faculty(request_entry.assigned_to.email, data, user_profile.user_type) # Faculty replies back to the comment
            else: # This is for the situation where there is no assigned to yet, and the faculty comments
                admin_user_profiles = UserProfile.objects.filter(user_type='admin')
                admin_user_ids = admin_user_profiles.values_list('user_id', flat=True)

                tsgUsers = User.objects.filter(id__in = admin_user_ids)
                tsgEmails = []
                for tsg in tsgUsers:
                    tsgEmails.append(tsg.email)
                comment_notif_faculty(tsgEmails, data, 'admin') 
        Comment.objects.create(
            request_entry=request_entry,
            comment=comment_text,
            user=user
        )
        
        if new_data:
            log_request_entry_changes(request_entry, user, new_data, user)

    return redirect('ticketing:request_details', request_id=pk)
class RequestForm(forms.ModelForm):
    class Meta:
        model = RequestEntry
        fields = ['requester']

class RequestFormView(generic.edit.FormView):
    template_name = "ticketing/new-form.html"
    form_class = RequestForm

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        vmtemplate_list = VMTemplates.objects.filter(is_lxc = 0).values_list('id', 'vm_name', 'storage')
        context['vmtemplate_list'] = list(vmtemplate_list)
        return context

# @login_required
# def redirect_based_on_user_type(request):
#     user_profile = request.user.userprofile
#     if user_profile.user_type == 'student':
#         return redirect('users:student_home')
#     elif user_profile.user_type == 'faculty':
#         return redirect('users:faculty_home')
#     elif user_profile.user_type == 'tsg':
#         return redirect('users:tsg_home')


#@login_required
def new_form_submit(request):
    # TODO: authenticate if valid user(logged in & faculty/tsg)
    print("submit form")
    if request.method == "POST":
        print("Inside the request.method post")
        # get data
        requester = get_object_or_404(User, username=request.user)
        data = request.POST
        template_id = data.get("template_id")
        cores = data.get("cores")
        ram = data.get("ram")
        has_internet = data.get("external_access") == 'true'
        date_needed = data.get ('date_needed')
        expiration_date = data.get('expiration_date')
        other_config = data.get("other_configs")
        use_case = data.get('use_case')
        is_recurring = data.get('recurring')
        vmTemplateID = VMTemplates.objects.get(id = template_id)
        # TODO: data verification

        if is_recurring: expiration_date = None
        
        # create request object
        new_request = RequestEntry.objects.create(
            requester = requester,
            template = vmTemplateID,
            cores = cores,
            ram = ram,
            # storage = storage,
            has_internet = has_internet,
            other_config = other_config,
            date_needed = date_needed,
            expiration_date = expiration_date
            # status = RequestEntry.Status.PENDING,
        )
        
        gVM_count = 0
        if use_case == 'CLASS_COURSE':
            for i in range(1, int(data['addCourseButtonClick']) + 1):
                course_code = data.get(f"course_code{i}")
                vm_count = data.get(f"vm_count{i}")
                if course_code is not None:
                    # If vm_count is not None, convert to int; otherwise, default to 0
                    vm_count_int = int(vm_count) if vm_count is not None else 0
                if course_code is not None:
                    RequestUseCase.objects.create(
                        request = new_request,
                        request_use_case = course_code,
                        vm_count = vm_count_int
                    )
            gVM_count += vm_count_int
        else:
            RequestUseCase.objects.create(
                    request = new_request,
                    request_use_case = use_case,
                    vm_count = data.get(f"vm_count1")
                )
            gVM_count = data.get(f"vm_count1")
        if has_internet:
            for i in range(1, int(data['addProtocolClicked']) + 1):
                protocol = data.get(f'protocol{i}')
                dest_ports = data.get(f'destination_port{i}')
                #description = data.get('description')
                print (f'{protocol}, {dest_ports}')
                if protocol and dest_ports: 
                    PortRules.objects.create(
                        request = new_request,
                        protocol = protocol,
                        dest_ports = dest_ports,
                        #description = description
                    )

        admin_user_profiles = UserProfile.objects.filter(user_type='admin')
        admin_user_ids = admin_user_profiles.values_list('user_id', flat=True)

        tsgUsers = User.objects.filter(id__in = admin_user_ids)
        tsgEmails = []
        for tsg in tsgUsers:
            tsgEmails.append(tsg.email)
        
        print (tsgEmails)
        data = {
            'vm_template_name' : vmTemplateID.vm_name,
            'use_case' : use_case,
            'vm_count' : gVM_count,
            'faculty_name' : requester.get_full_name()
        }
        comment_notif_tsg(tsgEmails, data)
    return JsonResponse({'status': 'ok'}, status=200)

def log_request_entry_changes(request_entry, changed_by, new_data, user):
    old_data = model_to_dict(request_entry)
    

    for field, value in old_data.items():
        if isinstance(value, datetime.date):
            old_data[field] = value.isoformat()
    
    print(old_data)
    for field, value in new_data.items():
        if isinstance(value, User):
            new_data[field] = value.id  
        elif isinstance(value, datetime.date):
            new_data[field] = value.isoformat()
        elif isinstance(value, VMTemplates):
            new_data[field] = value.id
    
    changes = {field: {'old': old_data[field], 'new': new_data[field]}
               for field in new_data if old_data[field] != new_data[field]}

    print(changes)
    RequestEntryAudit.objects.create(
        request_entry=request_entry,
        changed_by=changed_by,
        changes=json.dumps(changes)
    )
    loggedIn_user = get_object_or_404(User, username=user)
   
    for field, value in new_data.items():
        if field == 'assigned_to':
           setattr(request_entry, field, loggedIn_user) 
        elif field == 'template':
            vm_template = get_object_or_404(VMTemplates, id = value)
            setattr(request_entry, field, vm_template)
        else: 
            setattr(request_entry, field, value)
    request_entry.save()

def edit_form_submit(request):
    data = request.POST
    user = request.user
    request_entry_id = data.get("id")
    request_entry = get_object_or_404(RequestEntry, id = request_entry_id)
    newData = {}
    newvmTemplateID = VMTemplates.objects.get(id=data.get("template_id"))
    newData = {
            'template': newvmTemplateID,
            'cores': data.get("cores"),
            'ram': data.get("ram"),
            'has_internet': data.get("external_access") == 'true',
            'date_needed': data.get('date_needed'),
            'expiration_date': data.get('expiration_date'),
            'other_config': data.get("other_configs"),
        }
    newUseCase = data.get('use_case')
    addCourseButtonClicked = int(data.get("addCourseButtonClick"))

    print(newData)

    # TODO: Fix the protocol front end for the edit_request_html first and do the backend
    # For the protocol

    if newData['has_internet'] == True:
        addProtocolClicked = int(data.get('addProtocolClicked'))
        port_rules = PortRules.objects.filter(request_id = request_entry_id)
        last_index = 0
        overwrite_times = 0
        for i in range(1, addProtocolClicked + 1):
            protocol = data.get(f"protocol{i}")
            dest_ports = data.get(f"destination_port{i}")
            print (f"{protocol}, {dest_ports}, {len(port_rules)}, {i} , {last_index},{overwrite_times}")
            if protocol is not None:
                if i <= len(port_rules) or overwrite_times < len(port_rules):
                    if i <= len(port_rules): 
                        print ('overwriting the same row')
                        list_portRules = port_rules[i - 1]
                        last_index = i - 1
                    else: 
                        print ('overwriting the same row')
                        list_portRules = port_rules[last_index + 1]
                        last_index = i + 1
                    list_portRules.protocol = protocol
                    list_portRules.dest_ports = dest_ports
                    list_portRules.save()
                    overwrite_times += 1
                else:
                    PortRules.objects.create(
                        request=request_entry,
                        protocol=protocol,
                        dest_ports=dest_ports
                    )

        if len(port_rules) > addProtocolClicked:
            for i in range(addProtocolClicked, len(port_rules)):
                port_rules[i].delete()

    request_use_cases = RequestUseCase.objects.filter(request_id = request_entry_id)
    request_use_case = request_use_cases.first()
    

    #Changes getting the use cases data
    if request_use_case.request_use_case in ['RESEARCH', 'THESIS', 'TEST']:
        dbUseCase = request_use_case.request_use_case
    else:
        dbUseCase = 'CLASS_COURSE'

    print(dbUseCase)
    # Changes of use case
    if newUseCase in ['RESEARCH', 'THESIS', 'TEST'] and dbUseCase != 'CLASS_COURSE':
        print('3 to 3')
        request_use_case.request_use_case = newUseCase
        request_use_case.vm_count = data.get('vm_count1')
        request_use_case.save()
    elif dbUseCase == 'CLASS_COURSE' and newUseCase in ['RESEARCH', 'THESIS', 'TEST']:
        print('1 to 3')
        if request_use_cases.count() == 1:
            request_use_case.request_use_case = newUseCase
            request_use_case.vm_count = data.get('vm_count1')
            request_use_case.save()
        elif request_use_cases.count() > 1:
            request_use_cases.delete()
            RequestUseCase.objects.create(
                request=request_entry,
                request_use_case=newUseCase,
                vm_count= data.get('vm_count1')
            )
    elif newUseCase == 'CLASS_COURSE' :
        print ('1 to 1, 3 to 1')
        print (f'AddCourseButtonClicked: {addCourseButtonClicked}')
        listRequestUseCase = list(request_use_cases)
        last_index = 0
        overwrite_times = 0
        for i in range(1, addCourseButtonClicked + 1):
            course_code = data.get(f"course_code{i}")
            vm_count = data.get(f"vm_count{i}")
            print (f"{course_code}, {vm_count}, {len(request_use_cases)}, {i}, {last_index},{overwrite_times}")
            if course_code is not None:
                if i <= len(request_use_cases) or overwrite_times < len(request_use_cases):
                    if i <= len (request_use_cases):
                        print ('overwriting the same row')
                        list_request_use_case = listRequestUseCase[i - 1]
                        last_index = i - 1
                    else:
                        list_request_use_case = listRequestUseCase[last_index + 1]
                        last_index = i + 1
                    list_request_use_case.request_use_case = course_code
                    list_request_use_case.vm_count = vm_count
                    list_request_use_case.save()  
                    overwrite_times += 1
                else:
                    RequestUseCase.objects.create(
                        request=request_entry,
                        request_use_case=course_code,
                        vm_count=vm_count
                    )

        if len(request_use_cases) > addCourseButtonClicked:
            for i in range(addCourseButtonClicked, len(request_use_cases)):
                request_use_cases[i].delete()

    #Changes for the vm details
    log_request_entry_changes(request_entry, user, newData, user)

    return JsonResponse({'status': 'ok'}, status=200)

def request_confirm(request, request_id):

    # if request.method == 'POST':

    data = request.POST
    # node = data.get('node')

    node = "pve"
    request_entry = get_object_or_404(RequestEntry, id = request_id)
    request_entry.assigned_to = request.user
    to = request_entry.requester.email
    data = {
        "faculty_name" : request_entry.requester.get_full_name(),
        "id" : request_id
    }
    create_test_vm.delay(request.user.pk, request_id, node)
    testVM_notif_faculty (to, data)
    return redirect('ticketing:request_details', request_id)

def request_reject(request, id):

    request_entry = get_object_or_404(RequestEntry, pk=id)
    request_entry.status = RequestEntry.Status.REJECTED
    request_entry.save()
    to = request_entry.requester.email
    data = {
        "faculty_name" : request_entry.requester.get_full_name(),
        "id" : id
    }
    reject_notif_faculty(to, data)

    return HttpResponseRedirect(reverse("ticketing:index"))

def request_test_vm_ready(request, id):
    
    request_entry = get_object_or_404(RequestEntry, pk=id)
    request_entry.is_vm_tested = True
    request_entry.save()
    
    vm = get_object_or_404(VirtualMachines, request=request_entry)
    guacamole_connection = get_object_or_404(GuacamoleConnection, vm=vm)

    tsg_guacamole_username = get_object_or_404(GuacamoleUser, system_user=request_entry.requester).username
    faculty_guacamole_user = get_object_or_404(GuacamoleUser, system_user=request_entry.requester)

    guacamole.assign_connection_group(faculty_guacamole_user.username, guacamole_connection.connection_group_id)
    guacamole.revoke_connection_group(tsg_guacamole_username, guacamole_connection.connection_group_id)
    guacamole.revoke_connection(tsg_guacamole_username, guacamole_connection.connection_id)
    guacamole.assign_connection(faculty_guacamole_user.username, guacamole_connection.connection_id)

    guacamole_connection.user = get_object_or_404(GuacamoleUser, system_user=request_entry.requester)
    guacamole_connection.save()

    return redirect(f"/ticketing/{id}/details")
    
def confirm_test_vm(request, request_id):
    
    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    request_entry.status = RequestEntry.Status.ONGOING
    request_entry.save()

    processing_ticket.delay(request_id)

    return redirect('ticketing:request_details', request_id)
    # return redirect(f'/ticketing/{request_id}/details')

def accept_test_vm(request, request_id): #Where the faculty Accepts the test vm created by the TSG 

    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    request_entry.status = RequestEntry.Status.ACCEPTED
    request_entry.save()
    
    # request_use_case = RequestUseCase.objects.get(request = request_entry)
    # to  = request_entry.assigned_to.email
    # use_case = "Class Course" if request_use_case.request not in ['Thesis', 'Research', 'Test'] else request_use_case.request
    # vmCount = 0
    # if use_case == "Class Course":
    #     for case in request_use_case:
    #         vmCount += case.vm_count
    # else:
    #     vmCount = request_use_case.vm_count
    # data = {
    #     "id" : request_id,
    #     "faculty_name" : request_entry.requester.get_full_name(),
    #     "use_case" : use_case,
    #     "vm_count" : vmCount,
    # }

    # accept_notif_tsg(to, data)
    return redirect('ticketing:request_details', request_id)

def reject_test_vm(request, request_id):   
    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    request_entry.status = RequestEntry.Status.REJECTED
    request_entry.save()

    vm = get_object_or_404(VirtualMachines, request=request_entry)
    guacamole_connection = get_object_or_404(GuacamoleConnection, vm=vm)
    guacamole_connection.is_active = False
    guacamole_connection.save()
    guacamole.delete_connection_group(guacamole_connection.connection_group_id)

    if vm.is_active():

        proxmox.stop_vm(vm.node.name, vm.vm_id)

        vm.set_shutdown()

        proxmox.wait_for_vm_stop(vm.node.name, vm.vm_id)
    
    proxmox.delete_vm(vm.node.name, vm.vm_id)

    vm.set_destroyed()

    return HttpResponseRedirect(reverse("ticketing:index"))

def delete_request(request, request_id):

    delete_request_process.delay(request_id)

    return redirect('/ticketing')

def edit_request(request, request_id):
    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    request_use_cases = RequestUseCase.objects.filter(request_id=request_id)
    portRules = PortRules.objects.filter(request_id=request_id)
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

    comments = get_comments(request_entry)

    if comments.exists():
        context['comments'] = comments

    print(context)
    return render(request, 'ticketing/faculty_edit_request.html', context)

def get_comments(request_entry):
    return Comment.objects.filter(request_entry=request_entry).select_related("user").values(
            "comment",
            "user__first_name",
            "user__last_name",
            "date_time",
        ).order_by('date_time')

def new_form_container(request):
    container_template = VMTemplates.objects.filter(is_lxc = 1)
    context = {}
    context['container_template'] = container_template
    print (context['container_template'])
    return render (request, 'ticketing/new-form-container.html', context)

# def clear_credential(request):
#     print('clear_credential')
#     if request.method == 'POST':
#         print('clear_credential2')
#         if 'credentials' in request.session:
#             print('clear_credential3')
#             request.session.pop('credentials', None)
#             return JsonResponse({'status': 'success'})
#         return JsonResponse({'status': 'invalid method'}, status=405)
