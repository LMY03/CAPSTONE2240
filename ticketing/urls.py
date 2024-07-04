from django.urls import path

from . import views

app_name = "ticketing"
urlpatterns = [
    path("", views.request_list, name="index"),
    path("<int:request_id>/details/", views.request_details, name="request_details"),
    path("new-form/", views.RequestFormView.as_view(), name="new-form"),
    path('new-form-container/', views.new_form_container, name = 'new-form-container'),
    path("new-form-submit/", views.new_form_submit, name="new-form-submit"),
    path("request-confirm/<int:id>/", views.request_confirm, name="request-confirm"),
    path("request-reject/<int:id>/", views.request_reject, name="request-reject"),
    path('add_comment/<int:pk>/', views.add_comment, name='add_comment'),
    path('edit-form-submit/', views.edit_form_submit, name= 'edit_form_submit'),
    path('request_test_vm_ready/<int:id>', views.request_test_vm_ready, name='request_test_vm_ready'),
    path('confirm_test_vm/<int:id>', views.confirm_test_vm, name='confirm_test_vm'),
    path('reject_test_vm/<int:id>', views.reject_test_vm, name='reject_test_vm'),
    path('delete_request/<int:request_id>', views.delete_request, name='delete_request'),
    path('faculty_edit_request/<int:request_id>', views.edit_request, name = 'faculty_edit_request'),

    path("download_credentials", views.download_credentials, name="download_credentials"),
]