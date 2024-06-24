from django.urls import path

from . import views

app_name = "ansible"

urlpatterns = [
    path("", views.renders, name="form"),
    path("run", views.run, name="run"),
]