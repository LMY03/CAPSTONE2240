from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import RequestEntry

# Create your views here.
class IndexView(generic.ListView):
    template_name = "ticketing/request-list.html"
    context_object_name = "request_list"

    def get_queryset(self):
        return RequestEntry.objects.all()
    
class DetailView(generic.DetailView):
    model = RequestEntry
    template_name = "ticketing/detail.html"
    
class RequestForm(forms.ModelForm):
    class Meta:
        model = RequestEntry
        fields = ['requester_id']

class RequestFormView(generic.edit.FormView):
    template_name = "ticketing/new-form.html"
    form_class = RequestForm

def new_form_submit(request):

    # TODO: authenticate if valid user(logged in & faculty/tsg)

    if request.method == "POST":
        # get data
        data = request.POST
        requester_id = data.get("requester_id")
        template_id = data.get("template_id")
        cores = data.get("cores")
        ram = data.get("ram")
        storage = data.get("storage")
        has_internet = data.get("has_internet")
        
        print("-----------------------")
        print(data)

        # TODO: data verification

        # create request object

        new_request = RequestEntry(
            requester_id = requester_id,
            template_id = template_id,
            cores = cores,
            ram = ram,
            storage = storage,
            has_internet = has_internet,
            # status = RequestEntry.Status.PENDING,
        )
        new_request.save()

    return HttpResponseRedirect(reverse("ticketing:index"))

def request_confirm(request):
    if request.method == "POST":
        data = request.POST
        id = data.get("id")
        request_entry = RequestEntry.objects.get(pk=id)
        
        if data.get("action") == 'Accept':
            request_entry.status = RequestEntry.Status.CREATING
        
        if data.get("action") == 'For Revision':
            request_entry.template_id = data.get("template_id")
            request_entry.cores = data.get("cores")
            request_entry.ram = data.get("ram")
            request_entry.storage = data.get("storage")
            request_entry.has_internet = data.get("has_internet")
            request_entry.status = RequestEntry.Status.FOR_REVISION

        request_entry.save()
    return HttpResponseRedirect(reverse("ticketing:index"))