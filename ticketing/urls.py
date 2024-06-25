from django.urls import path

from . import views

app_name = "ticketing"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"), #request list
    path("new-form/", views.RequestFormView.as_view(), name="new-form"),
    path("new-form-submit/", views.new_form_submit, name="new-form-submit"),
    path("<int:pk>/details/", views.DetailView.as_view(), name="details"),
    path("request-confirm/<int:id>/", views.request_confirm, name="request-confirm"),
    path('add_comment/<int:pk>/', views.add_comment, name='add_comment'),
    path('edit-form-submit/', views.edit_form_submit, name= 'edit_form_submit'),
]