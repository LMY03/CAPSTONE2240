from typing import Any
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from .models import OSList
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import RequestEntry, Comment
from django.shortcuts import redirect


def login (request):
    return render(request, 'login.html')

# Create your views here.
class IndexView(generic.ListView):
    template_name = "ticketing/request-list.html"
    context_object_name = "request_list"

    def get_queryset(self):
        return RequestEntry.objects.select_related("template_id").values("status", "requester_id", "cores", "ram", "storage", "has_internet", "id", "template_id__os_name")
    
class DetailView(generic.DetailView):
    model = RequestEntry
    template_name = "ticketing/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        request_entry = get_object_or_404(RequestEntry, pk=pk)
        comments = Comment.objects.filter(request_entry=request_entry).order_by('-date_time')
        context['request_entry'] = {
            'details': request_entry,
            'comments' : comments
        }
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
        fields = ['requester_id']

class RequestFormView(generic.edit.FormView):
    template_name = "ticketing/new-form.html"
    form_class = RequestForm

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        os_list = OSList.objects.all().values_list('id', 'os_code', 'os_name')
        context['os_options'] = list(os_list)
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

@login_required
def new_form_submit(request):

    # TODO: authenticate if valid user(logged in & faculty/tsg)

    if request.method == "POST":
        # get data
        data = request.POST
        requester_id = request.user
        template_id = data.get("template_id")
        cores = data.get("cores")
        ram = data.get("ram")
        storage = data.get("storage")
        has_internet = data.get("has_internet") == 'true'
        use_case = data.get("use_case")
        other_config = data.get("other_configs")
        vm_count = data.get("vm_count")
        
        os = OSList.objects.get(id = template_id)
        print("-----------------------")
        print(data)

        # TODO: data verification

        # create request object

        new_request = RequestEntry(
            requester_id = requester_id,
            template_id = os,
            cores = cores,
            ram = ram,
            storage = storage,
            has_internet = has_internet,
            use_case = use_case,
            other_config = other_config,
            vm_count = vm_count,
            # status = RequestEntry.Status.PENDING,
        )
        new_request.save()

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
    return render (request, 'ticketing/request-list.html', {'request_list': request_list, 'status': status})