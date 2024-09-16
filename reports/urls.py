from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path('', views.index, name="index"),
    path('getVmList', views.getVmList, name="getVmList"),
    path('index_csv', views.index_csv, name="index_csv"),
    path('open_report_page', views.open_report_page, name="open_report_page"),
    page('report_gen', views.report_gen, name="report_gen")
]