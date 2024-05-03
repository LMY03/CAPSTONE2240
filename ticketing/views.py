from django.shortcuts import render
from .models import RequestEntry
from django import forms
from django.views.generic.edit import FormView

class RequestForm(forms.ModelForm):
    class Meta:
        model = RequestEntry
        fields = ['requester_id']

class RequestFormView(FormView):
    template_name = "ticketing/new-form.html"
    form_class = RequestForm


# Create your views here.
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
            has_internet = has_internet
        )
        new_request.save()

        # query request list
        request_list = RequestEntry.objects.all()

    return render(request, "ticketing/request-list.html", {"request_list": request_list})