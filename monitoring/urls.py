from django.urls import path

from . import views

app_name = "monitoring"

urlpatterns = [
    path('', views.index, name="index"),
    path('getdata/', views.getData, name="getData"),
    path('aggregateData/', views.aggregatedData, name="aggregateData")
]