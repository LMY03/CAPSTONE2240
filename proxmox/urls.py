from django.urls import path

from . import views

app_name = "proxmox"

urlpatterns = [
    path('', views.vm_list, name='index'),
    path('<int:vm_id>/details', views.vm_details, name='vm_details'),
    path('shutdown_vm/<int:vm_id>', views.shutdown_vm, name='shutdown_vm'),
    
    path("form", views.renders, name="form"),
    path("config_vm_disk", views.config_vm_disk, name="config_vm_disk"),
    path("clone_vm", views.clone_vm, name="clone_vm"),
    path("start_vm", views.start_vm, name="start_vm"),
    path("shutdown_vm", views.shutdown_vm, name="shutdown_vm"),
    path("delete_vm", views.delete_vm, name="delete_vm"),
    path("stop_vm", views.stop_vm, name="stop_vm"),
    path("status_vm", views.status_vm, name="status_vm"),
    path("ip_vm", views.ip_vm, name="ip_vm"),
    path("config_vm", views.config_vm, name="config_vm"),
    path("clone_lxc", views.clone_lxc, name="clone_lxc"),
    path("create_lxc", views.create_lxc, name="create_lxc"),
    path("start_lxc", views.start_lxc, name="start_lxc"),
    path("shutdown_lxc", views.shutdown_lxc, name="shutdown_lxc"),
    path("delete_lxc", views.delete_lxc, name="delete_lxc"),
    path("stop_lxc", views.stop_lxc, name="stop_lxc"),
    path("status_lxc", views.status_lxc, name="status_lxc"),
    path("ip_lxc", views.ip_lxc, name="ip_lxc"),
    path("config_lxc", views.config_lxc, name="config_lxc"),
    path("get_templates", views.get_templates, name="get_templates"),
    path("accept_vm/<int:vm_id>", views.accept_vm, name = 'accept_vm')
]