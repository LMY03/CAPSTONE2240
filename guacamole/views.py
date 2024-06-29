from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse

# from django.contrib.auth.models import User
# from . models import GuacamoleUser
from . import guacamole
from proxmox import proxmox

from guacamole.models import GuacamoleUser, GuacamoleConnection
from proxmox.models import VirtualMachines

# Create your views here.

# def create_guacamole_user(system_user):
#     guacamole_username = system_user.username
#     guacamole_password = system_user.password
#     guacamole_user = GuacamoleUser(user=system_user, username=guacamole_username, password=guacamole_password)
#     guacamole_user.save()
#     print(guacamole.create_user(guacamole_username, guacamole_password))

parent_identifier = "ROOT"

def launch_vm(request):
    print("launch vm ---------------------------")
    if request.method == "POST":

        data = request.POST
        vm_id = data.get("vm_id")
        vm = get_object_or_404(VirtualMachines, id=vm_id)
        node = vm.node
        
        
        guacamole_user = GuacamoleUser.objects.get(system_user=request.user)
        guacamole_username = guacamole_user.username
        guacamole_password = guacamole_user.password
        connection_id = get_object_or_404(GuacamoleConnection, vm=vm).connection_id
        # if proxmox.get_vm_status(node, vm_id) == "stopped" : proxmox.start_vm(node, vm_id)
        # hostname = proxmox.wait_and_get_ip(node, vm_id)
        # connection_details = guacamole.get_connection_parameter_details(connection_id)
        # if hostname != connection_details['hostname'] : guacamole.update_connection(connection_id, hostname)
        
        # redirect to new tab
        url =  guacamole.get_connection_url(connection_id, guacamole_username, guacamole_password)
        
        return JsonResponse({"redirect_url": url})
    
    return redirect("/users/student/vm/1")

def renders(request) : 
    return render(request, "guacamole.html")

def create_user(request) : 

    if request.method == "POST":

        data = request.POST
        username = data.get("username")
        password = data.get("password")

        status_code = guacamole.create_user(username, password)

        return render(request, "data.html", { "data" : status_code })
    
    return redirect("/guacamole")

def delete_user(request) : 

    if request.method == "POST":

        data = request.POST
        username = data.get("username")

        status_code = guacamole.delete_user(username)

        return render(request, "data.html", { "data" : status_code })
    
    return redirect("/guacamole")

def create_connection(request) : 

    if request.method == "POST":

        data = request.POST
        name = data.get("name")
        protocol = data.get("protocol")
        hostname = data.get("hostname")
        username = data.get("username")
        password = data.get("password")

        port = {
            'vnc': 5901,
            'rdp': 3389,
            'ssh': 22
        }.get(protocol)

        connection_id = guacamole.create_connection(name, protocol, port, hostname, username, password, parent_identifier)

        return render(request, "data.html", { "data" : connection_id })
    
    return redirect("/guacamole")

def delete_connection(request) : 

    if request.method == "POST":

        data = request.POST
        connection_id = data.get("connection_id")

        status_code = guacamole.delete_connection(connection_id)

        return render(request, "data.html", { "data" : status_code })
    
    return redirect("/guacamole")


def assign_connection(request) : 

    if request.method == "POST":

        data = request.POST
        username = data.get("username")
        connection_id = data.get("connection_id")

        status_code = guacamole.assign_connection(username, connection_id)

        return render(request, "data.html", { "data" : status_code })
    
    return redirect("/guacamole")


def revoke_connection(request) : 

    if request.method == "POST":

        data = request.POST
        username = data.get("username")
        connection_id = data.get("connection_id")

        status_code = guacamole.revoke_connection(username, connection_id)

        return render(request, "data.html", { "data" : status_code })
    
    return redirect("/guacamole")


def update_connection(request) : 

    if request.method == "POST":

        data = request.POST
        hostname = data.get("hostname")
        connection_id = data.get("connection_id")

        response = guacamole.update_connection(connection_id, hostname)

        return render(request, "data.html", { "data" : response })
    
    return redirect("/guacamole")

def get_connection_details(request) : 

    if request.method == "POST":

        data = request.POST
        connection_id = data.get("connection_id")

        data = guacamole.get_connection_details(connection_id)

        return render(request, "data.html", { "data" : data })
    
    return redirect("/guacamole")

def get_connection_parameter_details(request) : 

    if request.method == "POST":

        data = request.POST
        connection_id = data.get("connection_id")

        data = guacamole.get_connection_parameter_details(connection_id)

        return render(request, "data.html", { "data" : data })
    
    return redirect("/guacamole")

def create_connection_group(request) : 

    if request.method == "POST":

        data = request.POST
        name = data.get("name")

        connection = guacamole.create_connection_group(name)

        return render(request, "data.html", { "data" : connection })
    
    return redirect("/guacamole")

def assign_connection_group(request) : 

    if request.method == "POST":

        data = request.POST
        username = data['name']
        connection_group_id = data['id']

        connection = guacamole.assign_connection_group(username, connection_group_id)

        return render(request, "data.html", { "data" : connection })
    
    return redirect("/guacamole")

def assign_connection_group(request) : 

    if request.method == "POST":

        data = request.POST
        username = data['name']
        connection_group_id = data['id']

        connection = guacamole.revoke_connection_group(username, connection_group_id)

        return render(request, "data.html", { "data" : connection })
    
    return redirect("/guacamole")

def revoke_connection_group(request) : 

    if request.method == "POST":

        data = request.POST
        username = data['name']
        connection_group_id = data['id']

        connection = guacamole.revoke_connection_group(username, connection_group_id)

        return render(request, "data.html", { "data" : connection })
    
    return redirect("/guacamole")

def delete_connection_group(request) : 

    if request.method == "POST":

        data = request.POST
        connection_group_id = data['id']

        connection = guacamole.delete_connection_group(connection_group_id)

        return render(request, "data.html", { "data" : connection })
    
    return redirect("/guacamole")