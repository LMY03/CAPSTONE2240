from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path('', views.index, name="index"),
    path('reports', views.reports, name="reports"),
    # path('performance_gen', views.performance_gen, name="performance_gen"),
    path('getVmList', views.getVmList, name="getVmList"),
    # path('extract_general_stat', views.extract_general_stat, name="extract_general_stat"),
    # path('extract_detail_stat', views.extract_detail_stat, name="extract_detail_stat"),
    path('reports/formdata?', views.formdata, name="formdata"),
    path('reports/graphdata?', views.graphdata, name="graphdata"),


    # path('index_csv', views.index_csv, name="index_csv"),
    # path('open_report_page', views.open_report_page, name="open_report_page"),
    # path('report_gen', views.report_gen, name="report_gen")
    path('ticketing_report', views.render_ticketing_report, name="ticketing_report"),
    path('download_general_ticketing_report', views.download_general_ticketing_report, name="download_general_ticketing_report"),
]