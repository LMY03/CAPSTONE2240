from django.urls import path

from . import views

app_name = "guacamole"

urlpatterns = [
    path("", views.renders, name="form"),
    path("create_user", views.create_user, name="create_user"),
    path("delete_user", views.delete_user, name="delete_user"),
    path("create_connection", views.create_connection, name="create_connection"),
    path("delete_connection", views.delete_connection, name="delete_connection"),
    path("assign_connection", views.assign_connection, name="assign_connection"),
    path("revoke_connection", views.revoke_connection, name="revoke_connection"),
    path("update_connection", views.update_connection, name="update_connection"),
    path("get_connection_details", views.get_connection_details, name="get_connection_details"),
    path("get_connection_parameter_details", views.get_connection_parameter_details, name="get_connection_parameter_details"),
]