from typing import Any
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect ,render
from django.urls import reverse
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import JsonResponse
from decouple import config
import json, datetime

from guacamole import guacamole
from proxmox import views, proxmox
from pfsense.views import add_port_forward_rules, delete_port_forward_rules

from .models import RequestEntry, Comment, RequestUseCase, PortRules, UserProfile, RequestEntryAudit, VMTemplates
from proxmox.models import VirtualMachines, Nodes
from guacamole.models import GuacamoleConnection, GuacamoleUser

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

    context = {
        'request_entry': request_entry,
        'comments' : comments,
        'request_use_cases': request_use_cases,
    }
    request_entry.storage = request_entry.template.storage
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

    portRules = PortRules.objects.filter(request_id = request_id)
    context = {
        'request_entry': request_entry,
        'comments' : comments,
        'request_use_cases': request_use_cases,
        'total_request_details' : total_request_details,
        'port_rules' : portRules,
        'no_vm': get_total_no_of_vm(request_entry)
    }
    if request_entry.is_pending() : context['nodes'] = Nodes.objects.all().values_list('name', flat=True)
    if 'credentials' in request.session : request_entry.has_credentials = True
    request_entry.storage = request_entry.template.storage
    return render (request, 'ticketing/tsg_request_details.html', context=context)

@login_required
def add_comment(request, pk):
    request_entry = get_object_or_404(RequestEntry, pk=pk)
    if request.method == 'POST':
        user = request.user
        user_profile = get_object_or_404(UserProfile, user=user)
    
        new_data = {}
        
        if request_entry.assigned_to is None and user_profile.user_type == 'admin':
            new_data['assigned_to'] = user
        
        comment_text = request.POST.get('comment')
        
        if request_entry.status == RequestEntry.Status.PENDING:
            new_data['status'] = RequestEntry.Status.FOR_REVISION
        
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
        vmTemplateID = VMTemplates.objects.get(id = template_id)
        # TODO: data verification

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
        
        
        if use_case == 'CLASS_COURSE':
            for i in range(1, int(data['addCourseButtonClick']) + 1):
                course_code = data.get(f"course_code{i}")
                vm_count = data.get(f"vm_count{i}")
                if course_code is not None:
                    RequestUseCase.objects.create(
                        request = new_request,
                        request_use_case = course_code,
                        vm_count = vm_count
                    )
        else:
            RequestUseCase.objects.create(
                    request = new_request,
                    request_use_case = use_case,
                    vm_count = data.get(f"vm_count1")
                )

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

    request_entry = get_object_or_404(RequestEntry, pk=request_id)

    create_test_vm(request.user, request_id, node)

    request_entry.status = RequestEntry.Status.PROCESSING
    request_entry.fulfilled_by = request.user
    request_entry.save()

    return redirect('ticketing:request_details', request_id)

def request_reject(request, id):

    request_entry = get_object_or_404(RequestEntry, pk=id)
    request_entry.status = RequestEntry.Status.REJECTED
    request_entry.save()

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

def get_total_no_of_vm(request_entry):
    request_use_cases = RequestUseCase.objects.filter(request=request_entry).values('request_use_case', 'vm_count')
    total_no_of_vm = 0
    for request_use_case in request_use_cases : total_no_of_vm += int(request_use_case['vm_count'])
    return total_no_of_vm

def create_test_vm(tsg_user, request_id, node): 
    new_vm_id = views.generate_vm_ids(1)[0]
    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    vm_id = int(request_entry.template.vm_id)

    request_use_case = RequestUseCase.objects.filter(request=request_entry.pk).values('request_use_case', 'vm_count')[0]

    if request_entry.is_course(): vm_name = f"{request_use_case['request_use_case'].replace('_', '-')}"
    else: vm_name = f"{request_entry.get_request_type()}-{request_entry.requester.last_name}-{request_entry.id}"

    if get_total_no_of_vm(request_entry) != 1 : vm_name = f"{vm_name}-Group-1"

    cpu_cores = int(request_entry.cores)
    ram = int(request_entry.ram)
    
    vm = VirtualMachines.objects.create(
        vm_id=new_vm_id,
        vm_name=vm_name,
        cores=cpu_cores,
        ram=ram,
        storage=request_entry.template.storage,
        request=request_entry,
        node=get_object_or_404(Nodes, name=node),
    )
    upid = proxmox.clone_vm(node, vm_id, new_vm_id, vm_name)
    proxmox.wait_for_task(node, upid)
    proxmox.config_vm(node, new_vm_id, cpu_cores, ram)
    proxmox.start_vm(node, new_vm_id)
    ip_add = proxmox.wait_and_get_ip(node, new_vm_id)
    proxmox.shutdown_vm(node, new_vm_id)
    proxmox.wait_for_vm_stop(node, new_vm_id)

    vm.set_ip_add(ip_add)
    vm.set_shutdown()

    protocol = request_entry.template.guacamole_protocol
    port = {
        'vnc': 5901,
        'rdp': 3389,
        'ssh': 22
    }.get(protocol)

    tsg_gaucamole_user = get_object_or_404(GuacamoleUser, system_user=tsg_user)
    guacamole_connection_group_id = guacamole.create_connection_group(f"{request_id}")
    guacamole.assign_connection_group(tsg_gaucamole_user.username, guacamole_connection_group_id)
    guacamole_connection_id = guacamole.create_connection(vm_name, protocol, port, ip_add, config('DEFAULT_VM_USERNAME'), config('DEFAULT_VM_PASSWORD'), guacamole_connection_group_id)
    guacamole.assign_connection(tsg_gaucamole_user.username, guacamole_connection_id)

    # vm = VirtualMachines(
    #     vm_id=new_vm_id, 
    #     vm_name=vm_name, 
    #     cores=cpu_cores, 
    #     ram=ram, 
    #     storage=request_entry.template.storage, 
    #     ip_add=ip_add, 
    #     request=request_entry, 
    #     node=node,
    #     status=VirtualMachines.Status.SHUTDOWN
    # )
    # vm.save()
    GuacamoleConnection(user=get_object_or_404(GuacamoleUser, system_user=tsg_user), connection_id=guacamole_connection_id, connection_group_id=guacamole_connection_group_id, vm=vm).save()
    
def confirm_test_vm(request, request_id):

    request_entry = get_object_or_404(RequestEntry, pk=request_id)

    request.session['credentials'] = vm_provision(request_id)
    vms = VirtualMachines.objects.filter(request=request_entry)
    port_rules = PortRules.objects.filter(request=request_entry)
    if port_rules.exists():
        protocols = port_rules.values_list('protocol', flat=True)
        local_ports = port_rules.values_list('dest_ports', flat=True)
        ip_adds = vms.values_list('ip_add', flat=True)
        descrs = vms.values_list('vm_name', flat=True)
        add_port_forward_rules(request_id, protocols, local_ports, ip_adds, descrs) # pfsense
    
    request_entry.status = RequestEntry.Status.ONGOING
    request_entry.save()

    return redirect('ticketing:request_details', request_id)
    # return redirect(f'/ticketing/{request_id}/details')

def accept_test_vm(request, request_id):

    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    request_entry.status = RequestEntry.Status.ACCEPTED
    request_entry.save()
    
    return redirect('ticketing:request_details', request_id)
    # return redirect(f'/ticketing/{request_id}/details')

def download_credentials(request):
    details = request.session['credentials']
    usernames = details['usernames']
    passwords = details['passwords']
    # vm_users = details['vm_user']
    # vm_passs = details['vm_passs']

    # Create the content of the text file
    file_content = ["VM Credentials\n"]
    for username, password in zip(usernames, passwords):
        file_content.append(f"Username: {username}")
        file_content.append(f"Password: {password}")
        # file_content.append(f"VM_User: {vm_user}")
        # file_content.append(f"VM_Pass: {vm_pass}")
        file_content.append("-------------------------------")

    # Join the content into a single string with newlines
    file_content_str = "\n".join(file_content)
    print(file_content_str)

    # Create the HttpResponse object with the plain text content
    response = HttpResponse(file_content_str, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=details.txt'
    
    return response

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

def vm_provision(request_id):

    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    vm = get_object_or_404(VirtualMachines, request=request_entry)

    if vm.is_active():

        proxmox.shutdown_vm(vm.node.name, vm.vm_id)

        vm.set_shutdown()

        proxmox.wait_for_vm_stop(vm.node.name, vm.vm_id)
        
    request_use_cases = RequestUseCase.objects.filter(request=request_entry).values('request_use_case', 'vm_count')
    classnames = []
    total_no_of_vm = get_total_no_of_vm(request_entry) - 1
    
    for request_use_case in request_use_cases:
        for i in range(request_use_case['vm_count']):
                if request_entry.is_course(): vm_name = f"{request_use_case['request_use_case'].replace('_', '-')}"
                else: vm_name = f"{request_entry.get_request_type()}-{request_entry.requester.last_name}-{request_entry.id}"
                vm_name = f"{vm_name}-Group-{i + 1}"
                classnames.append(vm_name)
    classnames.pop(0)

    cpu_cores = int(request_entry.cores)
    ram = int(request_entry.ram)

    return views.vm_provision_process(vm.vm_id, classnames, total_no_of_vm, cpu_cores, ram, request_id)

def delete_request(request, request_id):
    request_entry = get_object_or_404(RequestEntry, pk=request_id)

    vms = VirtualMachines.objects.filter(request=request_entry)
    port_rules = PortRules.objects.filter(request=request_entry)
    if port_rules.exists() : delete_port_forward_rules(len(port_rules), vms.values_list('vm_name', flat=True)) # pfsense

    for vm in vms:
        if vm.is_active:

            proxmox.stop_vm(vm.node.name, vm.vm_id)

            vm.set_shutdown()

    for vm in vms:
        vm.set_destroyed()

        proxmox.wait_for_vm_stop(vm.node.name, vm.vm_id)
        proxmox.delete_vm(vm.node.name, vm.vm_id)

        guacamole_connection = get_object_or_404(GuacamoleConnection, vm=vm)
        guacamole_connection.is_active = False
        guacamole_connection.save()
        guacamole_user = guacamole_connection.user
        guacamole_user.is_active = False
        guacamole_user.save()

        system_user = guacamole_user.system_user
        system_user.username = f"{system_user.username}_{request_id}"
        system_user.is_active = 0
        system_user.save()
        guacamole.delete_user(guacamole_user.username)
    
    guacamole.delete_connection_group(guacamole_connection.connection_group_id)
    
    request_entry.status = RequestEntry.Status.DELETED
    request_entry.save()

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

def clear_credential(request):
    print('clear_credential')
    if request.method == 'POST':
        print('clear_credential2')
        if 'credentials' in request.session:
            print('clear_credential3')
            request.session.pop('credentials', None)
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'invalid method'}, status=405)