from typing import Any
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect ,render
from django.urls import reverse
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import JsonResponse
import json, datetime

from .models import RequestEntry, Comment, RequestUseCase, PortRules, UserProfile, RequestEntryAudit, VMTemplates

from guacamole.models import GuacamoleConnection, GuacamoleUser
from guacamole import guacamole
from proxmox import proxmox
from proxmox import views
from proxmox.models import VirtualMachines, VMUser

def login (request):
    return render(request, 'login.html')

# Create your views here.
class IndexView(generic.ListView):
    template_name = "ticketing/tsg_home.html"
    context_object_name = "request_list"

    def get_queryset(self):
        queryset = RequestEntry.objects.select_related("requester", "template").values(
            "status",
            "requester__first_name",
            "requester__last_name",
            "cores",
            "ram",
            "has_internet",
            "id",
            "template__vm_name"
        )
        #.order_by('-requestDate')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print(context['request_list'])
        return context
class DetailView(generic.DetailView):
    model = RequestEntry
    template_name = "ticketing/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        request_entry = get_object_or_404(RequestEntry, pk=pk)

        request_entry_details = RequestEntry.objects.select_related("requester", "template").values(
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
            #"vm_count",
        ).get(pk=pk)


        request_use_cases = RequestUseCase.objects.filter(request_id=pk)


        comments = Comment.objects.filter(request_entry=request_entry).order_by('-date_time')
        context['request_entry'] = {
            'details': request_entry_details,
            'comments' : comments,
            'request_use_case': request_use_cases
        }
        print(context)
        return context

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
        
        if request_entry.status != RequestEntry.Status.FOR_REVISION:
            new_data['status'] = RequestEntry.Status.FOR_REVISION
        
        Comment.objects.create(
            request_entry=request_entry,
            comment=comment_text,
            user=user
        )
        
        if new_data:
            log_request_entry_changes(request_entry, user, new_data, user)

    
    if user_profile.user_type == 'admin':
        return redirect('ticketing:details', pk=pk)
    else:
        return redirect('users:edit_request', request_id = pk)

class RequestForm(forms.ModelForm):
    class Meta:
        model = RequestEntry
        fields = ['requester']

class RequestFormView(generic.edit.FormView):
    template_name = "ticketing/new-form.html"
    form_class = RequestForm

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        vmtemplate_list = VMTemplates.objects.all().values_list('id', 'vm_name', 'storage')
        context['vmtemplate_list'] = list(vmtemplate_list)
        return context

@login_required
def redirect_based_on_user_type(request):
    user_profile = request.user.userprofile
    if user_profile.user_type == 'student':
        return redirect('users:student_home')
    elif user_profile.user_type == 'faculty':
        return redirect('users:faculty_home')
    elif user_profile.user_type == 'tsg':
        return redirect('users:tsg_home')


#@login_required
def new_form_submit(request):
    # TODO: authenticate if valid user(logged in & faculty/tsg)
    print("submit form")
    if request.method == "POST":
        print("Inside the request.method post")
        # get data
        requester = get_object_or_404(User, username=request.user)
        data = request.POST
        print("-----------------------")
        print(f"{data}")
        print("-----------------------")
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
                description = data.get('description')
                print (f'{protocol}, {dest_ports}, {description}')
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

def edit_form_submit (request):
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
        for i in range(1, addCourseButtonClicked + 1):
            course_code = data.get(f"course_code{i}")
            vm_count = data.get(f"vm_count{i}")
            print (f"{course_code}, {vm_count}, {len(request_use_cases)}, {i}")
            if i <= len(request_use_cases):
                print ('overwriting the same row')
                list_request_use_case = listRequestUseCase[i - 1]
                list_request_use_case.request_use_case = course_code
                list_request_use_case.vm_count = vm_count
                list_request_use_case.save()
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

def request_confirm(request, id):
    request_entry = get_object_or_404(RequestEntry, pk=id)
    request_entry.status = RequestEntry.Status.PROCESSING
    request_entry.save()

    # data = vm_provision(id)

    create_test_vm(request.user, id)

    # confirm_test_vm(id)

    return HttpResponseRedirect(reverse("ticketing:index"))

def request_test_vm_ready(request, id): 
    request_entry = get_object_or_404(RequestEntry, pk=id)
    request_entry.is_vm_tested = True
    request_entry.save()

    return redirect("/users/tsg/requests")

def get_total_no_of_vm(request_entry):
    request_use_cases = RequestUseCase.objects.filter(request=request_entry).values('request_use_case', 'vm_count')
    total_no_of_vm = 0
    for request_use_case in request_use_cases:
        total_no_of_vm += int(request_use_case['vm_count'])
    return total_no_of_vm

def create_test_vm(tsg_user, id): 
    new_vm_id = views.generate_vm_ids(1)[0]
    node = "pve"
    request_entry = get_object_or_404(RequestEntry, pk=id)
    vm_id = int(request_entry.template.vm_id)
    request_use_case = RequestUseCase.objects.filter(request=request_entry.pk).values('request_use_case', 'vm_count')[0]
    vm_name = f"{request_use_case['request_use_case'].replace('_', '-')}-Group-1"
    cpu_cores = int(request_entry.cores)
    ram = int(request_entry.ram)
    
    # upid = proxmox.clone_vm(node, vm_id, new_vm_id, vm_name)
    # proxmox.wait_for_task(upid)
    # proxmox.config_vm(node, new_vm_id, cpu_cores, ram)
    # proxmox.start_vm(node, new_vm_id)
    # ip_add = proxmox.wait_and_get_ip(node, new_vm_id)
    # proxmox.shutdown_vm(node, new_vm_id)

    ip_add = "10.10.10.1"

    # faculty_guacamole_username = get_object_or_404(GuacamoleUser, system_user=request_entry.requester).username
    # guacamole_connection_group_id = guacamole.create_connection_group(f"{id}")
    # guacamole.assign_connection_group(faculty_guacamole_username, guacamole_connection_group_id)
    # guacamole_connection_id = guacamole.create_connection(vm_name, "rdp", 3389, ip_add, "jin", "123456", guacamole_connection_group_id)
    # # Create System and Guacamole User
    # passwords = User.objects.make_random_password()
    # user = User(username=vm_name)
    # user.set_password(passwords)
    # user.save()
    # UserProfile.objects.create(user=user)
    # guacamole.assign_connection(vm_name, guacamole_connection_id)
    # guacamole.assign_connection(faculty_guacamole_username, guacamole_connection_id)

    tsg_gaucamole_user = get_object_or_404(GuacamoleUser, system_user=tsg_user)
    guacamole_connection_group_id = guacamole.create_connection_group(f"{id}")
    guacamole.assign_connection_group(tsg_gaucamole_user.username, guacamole_connection_group_id)
    guacamole_connection_id = guacamole.create_connection(vm_name, "rdp", 3389, ip_add, "jin", "123456", guacamole_connection_group_id)
    guacamole.assign_connection(tsg_gaucamole_user.username, guacamole_connection_id)

    vm = VirtualMachines(
        vm_id=new_vm_id, 
        vm_name=vm_name, 
        cores=cpu_cores, 
        ram=ram, 
        storage=request_entry.template.storage, 
        ip_add=ip_add, 
        request=request_entry, 
        node=node)
    vm.save()
    GuacamoleConnection(user=get_object_or_404(GuacamoleUser, system_user=tsg_user), connection_id=guacamole_connection_id, connection_group_id=guacamole_connection_group_id, vm=vm).save()
    VMUser.objects.create(vm=vm, username="jin", password="123456")
    
def confirm_test_vm(request, id):
    request_entry = get_object_or_404(RequestEntry, pk=id)
    # list = VirtualMachines.objects.get(request_id=id)  
    print(id)
    if get_total_no_of_vm(request_entry) != 1 : vm_provision(id) 
    request_entry.status = RequestEntry.Status.ONGOING
    request_entry.save()

    return redirect("/users/faculty/home")

def vm_provision(id):

    node = "pve"
    request_entry = get_object_or_404(RequestEntry, pk=id)
    vm = get_object_or_404(VirtualMachines, request=request_entry)
    if vm.status == VirtualMachines.Status.ACTIVE:
        # proxmox.shutdown_vm(vm.node, vm.vm_id)
        vm.status = VirtualMachines.Status.SHUTDOWN
        vm.save()
    request_use_cases = []
    vm_name = ""
    request_use_cases = RequestUseCase.objects.filter(request=request_entry.pk).values('request_use_case', 'vm_count')
    classnames = []
    total_no_of_vm = get_total_no_of_vm(request_entry) - 1
    
    for request_use_case in request_use_cases:
        vm_name = f"{request_use_case['request_use_case']}-Group-1"
        for i in range(request_use_case['vm_count']):
            # vm_name = f"{request_use_case['request_use_case'].replace('_', '-')}-Group-{i + 1}"
            if vm.vm_name != vm_name:
                classnames.append(f"{request_use_case['request_use_case'].replace('_', '-')}-Group-{i}")
        # total_no_of_vm += int(request_use_case['vm_count'])

    faculty_guacamole_username = get_object_or_404(GuacamoleUser, system_user=request_entry.requester).username
    guacamole_connection = get_object_or_404(GuacamoleConnection, vm=vm)
    guacamole.assign_connection_group(faculty_guacamole_username, guacamole_connection.connection_group_id)
    tsg_guacamole_username = get_object_or_404(GuacamoleUser, system_user=request_entry.requester).username
    guacamole.revoke_connection_group(tsg_guacamole_username, guacamole_connection.connection_group_id)
    
    # Create System and Guacamole User
    passwords = User.objects.make_random_password()
    user = User(username=vm_name)
    user.set_password(passwords)
    user.save()
    UserProfile.objects.create(user=user)
    guacamole.revoke_connection(tsg_guacamole_username, guacamole_connection.connection_id)
    guacamole.assign_connection(vm_name, guacamole_connection.connection_id)
    guacamole.assign_connection(faculty_guacamole_username, guacamole_connection.connection_id)
    guacamole_connection.user = get_object_or_404(GuacamoleUser, system_user=user)

    cpu_cores = int(request_entry.cores)
    ram = int(request_entry.ram)

    data =  views.vm_provision_process(node, vm.id, classnames, total_no_of_vm, cpu_cores, ram, id)

    return

def delete_vms(request, request_id):
    request_entry = get_object_or_404(RequestEntry, pk=request_id)

    vms = VirtualMachines.objects.filter(request=request_entry)
    print(vms)

    for vm in vms:
        if vm.status == VirtualMachines.Status.ACTIVE:
            # proxmox.stop_vm(vm.node, vm.vm_id)
            vm.status = VirtualMachines.Status.SHUTDOWN
            vm.save()

    for vm in vms:
        # proxmox.wait_for_vm_stop(vm.node, vm.vm_id)
        # proxmox.delete_vm(vm.node, vm.vm_id)
        vm.status = VirtualMachines.Status.DESTROYED
        vm.save()
        guacamole_connection = get_object_or_404(GuacamoleConnection, vm=vm)
        guacamole_connection.status = GuacamoleConnection.Status.DELETED
        guacamole_connection.save()
        guacamole_user = guacamole_connection.user
        guacamole_user.status = GuacamoleUser.Status.DELETED
        guacamole_user.save()
        system_user = guacamole_user.system_user
        system_user.is_active = 0
        system_user.save()
        
    request_entry.status = RequestEntry.Status.DELETED
    request_entry.save()

    return redirect('/users/faculty/home/')

def new_form_container (request):
    container_template = VMTemplates.objects.filter(is_lxc = 1)
    context = {}
    context['container_template'] = container_template
    print (context['container_template'])
    return render (request, 'ticketing/new-form-container.html', context)