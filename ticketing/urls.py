from django.urls import path

from . import views

app_name = "ticketing"
urlpatterns = [
    # path("", views.IndexView.as_view(), name="index"), #request list
    path("new-form/", views.RequestFormView.as_view(), name="new-form"), # TODO change function name
    path("new-form-submit/", views.new_form_submit, name="new-form-submit"),
    # path("<string:request_id>/details/", views.DetailView.as_view(), name="details"),
    # path("request-confirm/", views.request_confirm, name="request-confirm"), # TODO change function name
    # path("<string:request_id>/history/", views.HistoryView.as_view(), name="history"),
    # path("<string:request_id>/history/draft-<int:index>", views.HistoryDraftView.as_view(), name="history-draft")
]