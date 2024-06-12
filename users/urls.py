from django.urls import path

from . import views

app_name = "users"
urlpatterns = [
    path('home-filter/', views.home_filter_view, name='home-filter'),
    path('student/home/', views.student_home, name='student_home'),
    path('faculty/home/', views.faculty_home, name='faculty_home'),
    path('tsg/home/', views.tsg_home, name='tsg_home'),
    path('student/vm/<str:vm_id>/', views.vm_details, name='vm_details'),
    path('tsg/requests/', views.tsg_requests, name = 'vm_requests'),
    path('tsg/request_details/<int:request_id>', views.request_details, name = 'request_details'),
    path('faculty/vm_details/<str:vm_id>', views.faculty_vm_details, name = 'vm_details_faculty'),
    path('faculty/requests_list', views.faculty_request_list, name = 'faculty_request_list'),
]