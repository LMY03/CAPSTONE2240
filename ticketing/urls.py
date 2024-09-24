from django.urls import path

from . import views

app_name = "ticketing"
urlpatterns = [
    path("", views.request_list, name="index"),
    path("<int:request_id>/details/", views.request_details, name="request_details"),
    path("new-form/", views.RequestFormView.as_view(), name="new-form"),
    path('new-form-container/', views.new_form_container, name = 'new-form-container'),
    path("new-form-submit/", views.new_form_submit, name="new-form-submit"),
    path("request-confirm/<int:request_id>/", views.request_confirm, name="request-confirm"),
    path("request-reject/<int:id>/", views.request_reject, name="request-reject"),
    path('add_comment/<int:pk>/', views.add_comment, name='add_comment'),
    path('edit-form-submit/', views.edit_form_submit, name= 'edit_form_submit'),
    path('request_test_vm_ready/<int:id>', views.request_test_vm_ready, name='request_test_vm_ready'),
    path('confirm_test_vm/<int:request_id>', views.confirm_test_vm, name='confirm_test_vm'),
    path('accept_test_vm/<int:request_id>', views.accept_test_vm, name='accept_test_vm'),
    path('reject_test_vm/<int:request_id>', views.reject_test_vm, name='reject_test_vm'),
    path('delete_request/<int:request_id>', views.delete_request, name='delete_request'),
    path('faculty_edit_request/<int:request_id>', views.edit_request, name = 'faculty_edit_request'),
    path('submit_issue_ticket', views.submit_issue_ticket, name='submit_issue_ticket'),
    path('add_users/', views.add_users, name='add_users'),

    # path('clear_credential', views.clear_credential, name = 'clear_credential'),
    # path('download_credentials', views.download_credentials, name='download_credentials'),
]