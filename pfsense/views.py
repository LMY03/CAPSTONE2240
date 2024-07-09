from django.shortcuts import render, redirect

from . import pfsense

# Create your views here.

def renders(request):
    return render(request, 'pfsense.html')

def add_rule(request):

    if request.method == 'POST':
        data = pfsense.add_firewall_rule()
        # data = opnsense.get_firewall_rule("c423352c-d132-438f-be10-d86f6a429244")

        return render(request, 'data.html', { 'data' : data })

    return redirect('/opnense')

def get_rules(request):
    data = pfsense.get_rules()
    render(request, 'data.html', { 'data' : data })