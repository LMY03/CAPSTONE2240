from django.urls import path

from . import views

app_name = "opnsense"

urlpatterns = [
    path('', views.renders, name='index'),
    path('add_rule', views.add_rule, name='add_rule'),
]