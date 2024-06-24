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

from proxmox import proxmox
from guacamole import guacamole
from autotool import ansible

from .models import RequestEntry, Comment, RequestUseCase, GroupList, VMTemplates, UserProfile, RequestEntryAudit

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
            "vm_count",
            "template__storage"
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

    return redirect('ticketing:details', pk=pk)

class RequestForm(forms.ModelForm):
    class Meta:
        model = RequestEntry
        fields = ['requester']

class RequestFormView(generic.edit.FormView):
    template_name = "ticketing/new-form.html"
    form_class = RequestForm

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        vmtemplate_list = VMTemplates.objects.all().values_list('id', 'vm_name')
        context['vmtemplate_list'] = list(vmtemplate_list)
        #print(context)
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
    print ("new-form-submit")
    # TODO: authenticate if valid user(logged in & faculty/tsg)
    if request.method == "POST":
        print ("new-form-submit-post")
        # get data
        request.user = "jin"
        requester = get_object_or_404(User, username=request.user)
        data = request.POST
        template_id = data.get("template_id")
        cores = data.get("cores")
        ram = data.get("ram")
        # storage = data.get("storage")
        has_internet = data.get("has_internet") == 'true'
        date_needed = data.get ('date_needed')
        expiration_date = data.get('expiration_date')
        other_config = data.get("other_configs")
        vm_count = data.get("vm_count")
        print("-----------------------")
        print ("new-form-submit2")
        
        vmTemplateID = VMTemplates.objects.get(id = template_id)
        print("-----------------------")
        print(data)
        print("-----------------------")
        # TODO: data verification

        # create request object
        #print (vmTemplateID, requester)
        new_request = RequestEntry.objects.create(
            requester = requester,
            template = vmTemplateID,
            cores = cores,
            ram = ram,
            #storage = storage,
            has_internet = has_internet,
            other_config = other_config,
            vm_count = vm_count,
            date_needed = date_needed,
            expiration_date = expiration_date
            # status = RequestEntry.Status.PENDING,
        )
        
        new_request_use_case = []

        for i in range(1, int(data['addCourseButtonClick']) + 1):
            new_request_use_case.append(RequestUseCase.objects.create(
                request = new_request,
                request_use_case = data.get(f"course_code{i}")
            ))

        sections = data.getlist('sections')
        section_counts = {section: int(data.get(f'{section}_group_count', 0)) for section in sections}

        section_groups = {}

        for section in sections:
            group_count = section_counts[section]
            groups = {}

            for group in range(1, group_count + 1):
                group_key = f'student_user_{section}_{group}'
                students = [student.strip() for student in data.get(group_key, '').split(',') if student.strip()]

                groups[f'Group{group}'] = [student.strip() for student in students]

            section_groups[section] = groups
        print (section_groups)
        print("-----------------------")
        if data.get('useroption') == 'group' and data.get('use_case') == 'CLASS_COURSE':
            i = 0
            for section, groups in section_groups.items():
                j = 1
                print(f"Section: {section}, groups: {groups}, j:{j}")
                for group, students in groups.items():
                    print(f"Group: {group}, students: {students}")
                    for student in students:
                        if (student != ''):
                            print(f"Student:{student}")
                            grouplist = GroupList.objects.create(
                                user = student,
                                request_use_case = new_request_use_case[i],
                                group_number = j
                            )
                            print (f"Group List object: {grouplist.request_use_case}")
                    j += 1
                i += 1

    return redirect('users:faculty_home')

def log_request_entry_changes(request_entry, changed_by, new_data, user):
    old_data = model_to_dict(request_entry)
    

    for field, value in new_data.items():
        if isinstance(value, User):
            new_data[field] = value.id  
        elif isinstance(value, datetime.date):
            new_data[field] = value.isoformat()
    
    changes = {field: {'old': old_data[field], 'new': new_data[field]}
               for field in new_data if old_data[field] != new_data[field]}


    RequestEntryAudit.objects.create(
        request_entry=request_entry,
        changed_by=changed_by,
        changes=json.dumps(changes)
    )
    loggedIn_user = get_object_or_404(User, username=user)
   
    for field, value in new_data.items():
        if field == 'assigned_to':
           setattr(request_entry, field, loggedIn_user) 
        else: 
            setattr(request_entry, field, value)
    request_entry.save()

def request_confirm(request, id):
    request_entry = get_object_or_404(RequestEntry, pk=id)
    request_entry.status = RequestEntry.Status.PROCESSING
    request_entry.save()

    vm_provision(id)

    return HttpResponseRedirect(reverse("ticketing:index"))

def vm_provision_process(node, vm_id, classname, no_of_vm, cpu_cores, ram):

    protocol = "rdp"
    port = {
        'vnc': 5901,
        'rdp': 3389,
        'ssh': 22
    }.get(protocol)
    username = "jin"
    password = "123456"
    parent_identifier = "ROOT"

    upids = []
    new_vm_id = []
    hostname = []
    guacamole_connection_id = []
    guacamole_username = []
    guacamole_password = []

    for i in range(no_of_vm):
        # clone vm
        new_vm_id.append(vm_id + i + 1)
        upids.append(proxmox.clone_vm(node, vm_id, new_vm_id[i])['data'])

    for i in range(no_of_vm):
        # wait for vm to clone
        proxmox.wait_for_task(node, upids[i])
        # change vm configuration
        proxmox.config_vm(node, new_vm_id[i], cpu_cores, ram)
        # start vm
        proxmox.start_vm(node, new_vm_id[i])

    
    for i in range(no_of_vm):
        # wait for vm to start
        proxmox.wait_for_vm_start(node, new_vm_id[i])
        hostname.append(proxmox.wait_and_get_ip(node, new_vm_id[i]) )
        # create connection
        guacamole_username.append(f"{classname}-{i}")
        # guacamole_password.append(User.objects.make_random_password())
        guacamole_password.append("123456")
        guacamole_connection_id.append(guacamole.create_connection(guacamole_username[i], protocol, port, hostname[i], username, password, parent_identifier))
        guacamole.create_user(guacamole_username[i], guacamole_password[i])
        guacamole.assign_connection(guacamole_username[i], guacamole_connection_id[i])

        # set hostname and label in netdata
    vm_user = []
    vm_name = []
    label = []

    for i in range(no_of_vm):
        vm_user.append("jin")
        vm_name.append(classname + "-" + str(i))
        label.append(classname)

    ansible.run_playbook("netdata_conf.yml", hostname, vm_user, vm_name, label)

    return { 
        'vm_id' : new_vm_id, 
        'guacamole_connection_id' : guacamole_connection_id, 
        'guacamole_username' : guacamole_username
    }
    
def vm_provision(id):

    node = "pve"
    request_entry = get_object_or_404(RequestEntry, pk=id)
    print(request_entry)

    vm_id = int(request_entry.template.vm_id)
    request_use_case = get_object_or_404(RequestUseCase, pk=request_entry.id)
    classname = request_use_case.request_use_case
    no_of_vm = int(request_entry.vm_count)
    cpu_cores = int(request_entry.cores)
    ram = int(request_entry.ram)

    print("-------------------------------")
    print(vm_id)
    print(classname)
    print(no_of_vm)
    print(cpu_cores)
    print(ram)
    print("-------------------------------")

    data = vm_provision_process(node, vm_id, classname, no_of_vm, cpu_cores, ram)