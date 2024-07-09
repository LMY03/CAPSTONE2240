from django.urls import path

from . import views

app_name = "pfsense"

urlpatterns = [
    path('', views.renders, name='index'),
    path('add_rule', views.add_rule, name='add_rule'),
    path('get_rules', views.get_rules, name='get_rules'),
]