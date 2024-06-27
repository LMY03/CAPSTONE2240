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

from .models import RequestEntry, Comment, RequestUseCase, PortRules, UserProfile, RequestEntryAudit

from proxmox import views
from proxmox.models import VMTemplates, VirtualMachines

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
            "template__vm__vm_name"
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
        vmtemplate_list = VMTemplates.objects.all().values_list('id', 'vm__vm_name')
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
    print ("new-form-submit")
    # TODO: authenticate if valid user(logged in & faculty/tsg)
    if request.method == "POST":
        print ("new-form-submit-post")
        # get data
        #request.user = "jin"
        request.user = "faculty" # static
        requester = get_object_or_404(User, username=request.user)
        data = request.POST
        template_id = data.get("template_id")
        cores = data.get("cores")
        ram = data.get("ram")
        storage = data.get("storage")
        has_internet = data.get("external_access") == 'true'
        date_needed = data.get ('date_needed')
        expiration_date = data.get('expiration_date')
        other_config = data.get("other_configs")
        use_case = data.get('use_case')
        #vm_count = data.get("vm_count")
        
        vmTemplateID = VMTemplates.objects.get(id = template_id)
        print("-----------------------")
        print(f"{data}")
        print("-----------------------")
        # TODO: data verification

        # create request object
        new_request = RequestEntry.objects.create(
            requester = requester,
            template = vmTemplateID,
            cores = cores,
            ram = ram,
            #storage = storage,
            has_internet = has_internet,
            other_config = other_config,
            date_needed = date_needed,
            expiration_date = expiration_date
            # status = RequestEntry.Status.PENDING,
        )
        
        
        if use_case == 'CLASS_COURSE':
            for i in range(1, int(data['addCourseButtonClick']) + 1):
                RequestUseCase.objects.create(
                    request = new_request,
                    request_use_case = data.get(f"course_code{i}"),
                    vm_count = data.get(f"vm_count{i}")
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
                PortRules.objects.create(
                    request = new_request,
                    protocol = protocol,
                    dest_ports = dest_ports,
                    description = description
                )
        # sections = data.getlist('sections')
        # section_counts = {section: int(data.get(f'{section}_group_count', 0)) for section in sections}

        # section_groups = {}

        # for section in sections:
        #     group_count = section_counts[section]
        #     groups = {}

        #     for group in range(1, group_count + 1):
        #         group_key = f'student_user_{section}_{group}'
        #         students = [student.strip() for student in data.get(group_key, '').split(',') if student.strip()]

        #         groups[f'Group{group}'] = [student.strip() for student in students]

        #     section_groups[section] = groups
        # print (section_groups)
        # print("-----------------------")
        # if data.get('useroption') == 'group' and data.get('use_case') == 'CLASS_COURSE':
        #     i = 0
        #     for section, groups in section_groups.items():
        #         j = 1
        #         print(f"Section: {section}, groups: {groups}, j:{j}")
        #         for group, students in groups.items():
        #             print(f"Group: {group}, students: {students}")
        #             for student in students:
        #                 if (student != ''):
        #                     print(f"Student:{student}")
        #                     grouplist = GroupList.objects.create(
        #                         user = student,
        #                         request_use_case = new_request_use_case[i],
        #                         group_number = j
        #                     )
        #                     print (f"Group List object: {grouplist.request_use_case}")
        #             j += 1
        #         i += 1

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

def request_confirm(request, id):
    request_entry = get_object_or_404(RequestEntry, pk=id)
    request_entry.status = RequestEntry.Status.PROCESSING
    request_entry.save()

    vm_provision(id)

    return HttpResponseRedirect(reverse("ticketing:index"))
    
def vm_provision(id):

    node = "pve"
    request_entry = get_object_or_404(RequestEntry, pk=id)

    vm_id = int(request_entry.template.vm.vm_id)
    request_use_cases = []
    request_use_cases = RequestUseCase.objects.filter(request=request_entry.pk).values('request_use_case', 'vm_count')
    classnames = []
    total_no_of_vm = 0
    for request_use_case in request_use_cases:
        for i in range(request_use_case['vm_count']):
            classnames.append(f"{request_use_case['request_use_case'].replace('_', '-')}-Group-{i + 1}")
        total_no_of_vm += int(request_use_case['vm_count'])

    cpu_cores = int(request_entry.cores)
    ram = int(request_entry.ram)

    data = views.vm_provision_process(node, vm_id, classnames, total_no_of_vm, cpu_cores, ram)

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