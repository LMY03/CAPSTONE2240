from django.urls import path

from . import views

from guacamole.views import launch_vm
from proxmox.views import shutdown_vm
from ticketing.views import delete_vms, vm_provision

app_name = "users"
urlpatterns = [
    path('home-filter/', views.home_filter_view, name='home-filter'),
    path('student/home/', views.student_home, name='student_home'),
    path('faculty/home/', views.faculty_home, name='faculty_home'),
    path('tsg/home/', views.tsg_home, name='tsg_home'),
    path('student/vm/<str:vm_id>/', views.vm_details, name='vm_details'),
    path('student/vm_launch/', launch_vm, name='launch_vm'),
    path('shutdown_vm/', shutdown_vm, name='shutdown_vm'),
    path('tsg/requests/', views.tsg_requests, name = 'vm_requests'),
    path('tsg/request_details/<int:request_id>', views.tsg_request_details, name = 'request_details'),
    path('faculty/vm_details/<str:vm_id>', views.faculty_vm_details, name = 'vm_details_faculty'),
    path('faculty/requests_list', views.faculty_request_list, name='faculty_request_list'),
    path('faculty/request_details/<int:request_id>', views.faculty_request_details, name = 'faculty_request_details'),
    path('faculty/edit_request/<str:request_id>', views.edit_request, name = 'faculty_edit_request'),
    path('delete_vms/<int:request_id>', delete_vms, name='delete_vms'),
    path('login', views.login_view, name = "login"),
]