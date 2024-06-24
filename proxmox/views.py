import time

from django.shortcuts import redirect, render

from . import proxmox

# Create your views here.

node = "pve"

def renders(request) : 
    return render(request, "proxmox.html")

def clone_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")
        new_vm_id = data.get("newid")

        response = proxmox.clone_vm(node, vmid, new_vm_id)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def start_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.start_vm(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def shutdown_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.shutdown_vm(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def delete_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.delete_vm(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def stop_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.stop_vm(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def status_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        status = proxmox.get_vm_status(node, vmid)

        return render(request, "data.html", { "data" : status })
        
    return redirect("/proxmox")

def ip_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        ip = proxmox.get_vm_ip(node, vmid)

        return render(request, "data.html", { "data" : ip })
        
    return redirect("/proxmox")

def config_vm(request) : 

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")
        cpu_cores = data.get("cpu")
        memory = data.get("memory")

        response = proxmox.config_vm(node, vmid, cpu_cores, memory)

        return render(request, "data.html", { "data" : response })
    
    return redirect("/proxmox")

def clone_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")
        new_vm_id = data.get("newid")

        response = proxmox.clone_lxc(node, vmid, new_vm_id)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def start_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.start_lxc(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def shutdown_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.shutdown_lxc(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def delete_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.delete_lxc(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def stop_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.stop_lxc(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def status_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        status = proxmox.get_lxc_status(node, vmid)# [status]

        return render(request, "data.html", { "data" : status })
        
    return redirect("/proxmox")

def ip_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        ip = proxmox.wait_and_get_lxc_ip(node, vmid)

        return render(request, "data.html", { "data" : ip })
        
    return redirect("/proxmox")

def config_lxc(request) : 

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")
        cpu_cores = data.get("cpu")
        memory = data.get("memory")

        response = proxmox.config_lxc(node, vmid, cpu_cores, memory)

        return render(request, "data.html", { "data" : response })
    
    return redirect("/proxmox")