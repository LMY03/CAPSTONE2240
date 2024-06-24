from django.shortcuts import redirect, render

from . import guacamole

# Create your views here.

parent_identifier = "ROOT"

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