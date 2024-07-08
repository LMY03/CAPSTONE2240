from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from ticketing.models import RequestEntry, Comment, RequestUseCase, VMTemplates
from proxmox.models import VirtualMachines

from guacamole.models import GuacamoleUser, GuacamoleConnection

# Create your views here.
def login_view(request):
    data = request.POST
    username = data.get("username")
    password = data.get("password")
    
    user = authenticate(request, username=username, password=password)
        
    if user is not None:
        # Log in the user
        login(request, user)
        return redirect('dashboard')
        # return render_home(request)
        # user_profile = request.user.userprofile
        # if user_profile.user_type == 'student':
        #     return redirect('users:student_home')
        # elif user_profile.user_type == 'faculty':
        #     return redirect('users:faculty_home')
        # elif user_profile.user_type == 'admin':
        #     return redirect('users:tsg_home')
    else:
        # Handle invalid login
        return render(request, 'users/login.html', {'error': 'Invalid username or password'})

# Not Working
@login_required
def render_home(request):
    user_role = request.user.userprofile.user_type
    if user_role == 'student': return student_home(request)
    elif user_role == 'faculty': return faculty_home(request)
    elif user_role == 'admin': return tsg_home(request)

def home_filter_view(request):
    status = request.GET.get('status')
    request_list = RequestEntry.objects.filter(status=status)
    print(request_list)
    return render(request, 'ticketing/tsg_request_list.html', {'request_entries': request_list, 'status': status})

def get_student_vm():
    # Get the list of VM IDs from VMTemplates
    template_vm_ids = VMTemplates.objects.values_list('vm_id', flat=True)
    # Filter VirtualMachines to exclude those in VMTemplates and with status 'DELETED'
    return list(VirtualMachines.objects.exclude(id__in=template_vm_ids).exclude(status='DELETED').order_by('id').values())

# def student_home(request):

#     user = request.user
#     context = { 'vm_data' : GuacamoleConnection.objects.get(user=GuacamoleUser.objects.get(system_user=user)).vm }
    
#     return render(request, "users/student_vm_details.html", context)

@login_required
def student_home(request):
    guacamole_user = get_object_or_404(GuacamoleUser, system_user=request.user)
    guacamole_connection = get_object_or_404(GuacamoleConnection, user=guacamole_user)
    return render(request, 'users/student_home.html', {'vm': guacamole_connection.vm })

@login_required
def faculty_home(request):
    vm_list = []
    request_entries = RequestEntry.objects.filter(requester=request.user, is_vm_tested=True).exclude(status=RequestEntry.Status.DELETED).order_by('-id')
    
    for request_entry in request_entries:
        vm_list += VirtualMachines.objects.filter(request=request_entry).exclude(is_lxc=True, status=VirtualMachines.Status.DESTROYED)

    return render(request, 'users/faculty_home.html', {'data': vm_list })
    
@login_required
def tsg_home(request):
    request_entry = RequestEntry.objects.filter(status = 'PENDING')
    count = request_entry.count()
    context = {}
    context['open_request_count'] = count
    return render(request, 'users/tsg_home.html', context)


@login_required
def vm_details(request, vm_id):
    vm_data = VirtualMachines.objects.get(id=vm_id)
    # guacamole_connection = GuacamoleConnection.objects.get(vm=vm_data)
    # print("guacamole_connection")
    # print(guacamole_connection)
    context = {
        'vm_data': vm_data,
        'data' : get_student_vm(),
        # 'guacamole_connection' : guacamole_connection
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
        ).order_by('-id')
    # context['request_list'] = datas
    context = {'request_list': datas}
    print (context)
    return render (request, 'users/tsg_requests.html', context= context)

def tsg_request_details (request, request_id):
    request_entry = get_object_or_404(RequestEntry, pk=request_id)

    request_use_cases = RequestUseCase.objects.filter(request=request_entry)

    for request_use_case in request_use_cases:
        if request_use_case.request_use_case == 'RESEARCH' : request_entry.use_case = 'Research'
        elif request_use_case.request_use_case == 'THESIS' : request_entry.use_case = 'Thesis'
        elif request_use_case.request_use_case == 'TEST' : request_entry.use_case = 'Test'
        else: 
            request_entry.use_case = 'Class Course'
            request_entry.section_count = request_use_cases.count()



    if request_entry.status == RequestEntry.Status.PROCESSING: request_entry.vm_id = get_object_or_404(VirtualMachines, request=request_entry)

    comments = Comment.objects.filter(request_entry=request_entry).order_by('-date_time')
    context = {
        'request_entry': request_entry,
        'comments' : comments,
        'request_use_cases': request_use_cases,
    }
    return render (request, 'users/tsg_request_details.html', context = context)

def faculty_request_details (request, request_id):
    request_entry = get_object_or_404(RequestEntry, pk=request_id)

    request_use_cases = RequestUseCase.objects.filter(request=request_entry)

    for request_use_case in request_use_cases:
        if request_use_case.request_use_case == 'RESEARCH' : request_entry.use_case = 'Research'
        elif request_use_case.request_use_case == 'THESIS' : request_entry.use_case = 'Thesis'
        elif request_use_case.request_use_case == 'TEST' : request_entry.use_case = 'Test'
        else: request_entry.use_case = 'Class Course'

    if request_entry.status == RequestEntry.Status.PROCESSING: request_entry.vm_id = get_object_or_404(VirtualMachines, request=request_entry).id

    comments = Comment.objects.filter(request_entry=request_entry).order_by('-date_time')
    context = {
        'request_entry': request_entry,
        'comments' : comments,
        'request_use_cases': request_use_cases,
    }
    request_entry.storage = request_entry.template.storage
    return render (request, 'users/faculty_request_details.html', context = context)

def faculty_vm_details (request, vm_id):
    context ={
        'vm_id' : vm_id,
    }
    return render (request, 'users/faculty_vm_details.html', context = context)

def faculty_request_list(request):
    user = get_object_or_404(User, username=request.user.username)
    request_entries = RequestEntry.objects.filter(requester=user).order_by('-id')

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

        vm_list = VirtualMachines.objects.filter(request=request_entry)
        if vm_list.exists() : request_entry.vm_id = vm_list[0].id

    return render(request, 'users/faculty_request_list.html', { 'request_entries': request_entries })

def faculty_vm_list(request):
    request_entries = RequestEntry.objects.filter(requester=request.user).exclude(is_vm_tested=False).exclude(status=RequestEntry.Status.DELETED).order_by('-id')
    vm_list = []
    for request_entry in request_entries:
        vm_list.append(VirtualMachines.objects.filter(request=request_entry).exclude(status=VirtualMachines.Status.DESTROYED).order_by('id'))
    return render(request, 'users/faculty_vm_list.html', {'data': vm_list})

    
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
