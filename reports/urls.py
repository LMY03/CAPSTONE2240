from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path('', views.index, name="index"),
    path('reports', views.reports, name="reports"),
    path('getVmList', views.getVmList, name="getVmList"),
    path('formdata', views.formdata, name="formdata"),
    path('graphdata', views.graphdata, name="graphdata"),

    path('ticketing_report', views.render_ticketing_report, name="ticketing_report"),
    path('download_general_ticketing_report', views.download_general_ticketing_report, name="download_general_ticketing_report"),
]