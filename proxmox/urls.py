from django.urls import path

from . import views

app_name = "proxmox"

urlpatterns = [
    path('', views.vm_list, name='index'),
    path('<int:vm_id>/details', views.vm_details, name='vm_details'),
    path('shutdown_vm/<int:vm_id>', views.perform_shutdown, name='shutdown_vm'),
]