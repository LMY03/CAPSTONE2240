from django.shortcuts import render, redirect

from . import opnsense

# Create your views here.

def renders(request):
    return render(request, 'opnsense.html')

def add_rule(request):

    if request.method == 'POST':
        data = opnsense.add_firewall_rule()
        # data = opnsense.get_firewall_rule("c423352c-d132-438f-be10-d86f6a429244")

        return render(request, 'data.html', { 'data' : data })

    return redirect('/opnense')