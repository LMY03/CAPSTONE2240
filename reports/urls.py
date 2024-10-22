from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path('', views.index, name="index"),

    path('system/', views.system_report, name="system_report"),
    path('subject/', views.subject_report, name="subject_report"), 
    path('vm/', views.vm_report, name="vm_report"),

    path('getVmList', views.getVmList, name="getVmList"),
    path('formdata', views.formdata, name="formdata"),
    path('graphdata', views.graphdata, name="graphdata"),

    path('ticketing_report', views.render_ticketing_report, name="ticketing_report"),
    path('download_general_ticketing_report', views.download_general_ticketing_report, name="download_general_ticketing_report"),
]