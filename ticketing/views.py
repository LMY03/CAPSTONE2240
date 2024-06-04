from typing import Any
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from .models import VMTemplates
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import RequestEntry, Comment, RequestUseCase, GroupList
from django.shortcuts import redirect
import json

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
        # Fetch the RequestEntry object
        request_entry = get_object_or_404(RequestEntry, pk=pk)

        # Get the details you need from the request_entry
        request_entry_details = RequestEntry.objects.select_related("requester", "template").values(
            "status",
            "requester__first_name",
            "requester__last_name",
            "cores",
            "ram",
            "storage",
            "has_internet",
            "id",
            "template__vm_name",
            "use_case",
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
        print(context)
        return context

@login_required
def add_comment(request, pk):
    request_entry = get_object_or_404(RequestEntry, pk=pk)
    if request.method == 'POST':
        user = User.objects.get(username = request.user)
        comment_text = request.POST.get('comment')
        request_entry.status = RequestEntry.Status.FOR_REVISION
        Comment.objects.create(
            request_entry=request_entry,
            comment=comment_text,
            user=user
        )
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
        return redirect('ticketing:student_home')
    elif user_profile.user_type == 'faculty':
        return redirect('ticketing:faculty_home')
    elif user_profile.user_type == 'tsg':
        return redirect('ticketing:tsg_home')


@login_required
def student_home(request):
    return render(request, 'ticketing/student_home.html')

@login_required
def faculty_home(request):
    return render(request, 'faculty_home.html')

@login_required
def tsg_home(request):
    return render(request, 'tsg_home.html')

#@login_required
def new_form_submit(request):

    # TODO: authenticate if valid user(logged in & faculty/tsg)
    if request.method == "POST":
        # get data
        requester = get_object_or_404(User, username=request.user)
        data = request.POST
        template_id = data.get("template_id")
        cores = data.get("cores")
        ram = data.get("ram")
        storage = data.get("storage")
        has_internet = data.get("has_internet") == 'true'
        date_needed = data.get ('date_needed')
        expiration_date = data.get('expiration_date')
        other_config = data.get("other_configs")
        vm_count = data.get("vm_count")
        
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
            storage = storage,
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
                            try:
                                user = User.objects.get(email=student)
                            except User.DoesNotExist:
                                usernameSplit = student.split('@')
                                user = User.objects.create_user(email=student, password='', username = usernameSplit[0])
                            grouplist = GroupList.objects.create(
                                user = user,
                                request_use_case = new_request_use_case[i],
                                group_number = j
                            )
                            print (f"Group List object: {grouplist.request_use_case}")
                    j += 1
                i += 1

    return HttpResponseRedirect(reverse("ticketing:index"))

def request_confirm(request, id):
    request_entry = get_object_or_404(RequestEntry, pk=id)
    request_entry.status = RequestEntry.Status.CREATING
    request_entry.save()
    return HttpResponseRedirect(reverse("ticketing:index"))

# def revise_request(request, id):
#     data = request.POST
#     request_entry = get_object_or_404(RequestEntry, pk=id)
#     request_entry.status = RequestEntry.Status.FOR_REVISION
#     request_entry.revision_comments = data.get("comment")
#     request_entry.save()
#     return HttpResponseRedirect(reverse("ticketing:index"))

def home_filter_view (request):
    status = request.GET.get('status')
    request_list = RequestEntry.objects.filter(status = status)
    return render (request, 'ticketing/tsg_home.html', {'request_list': request_list, 'status': status})