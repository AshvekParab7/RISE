from django.urls import path

from .views import (
    ExamScheduleUploadConfirmView,
    ExamScheduleUploadCreateView,
    ExamScheduleUploadDetailView,
    NextActionView,
    OverviewView,
    PlanCommitView,
    PlanPreviewView,
)

urlpatterns = [
    path('overview/', OverviewView.as_view()),
    path('next-action/', NextActionView.as_view()),
    path('plan/preview/', PlanPreviewView.as_view()),
    path('plan/commit/', PlanCommitView.as_view()),
    path('exam-schedule-uploads/', ExamScheduleUploadCreateView.as_view()),
    path('exam-schedule-uploads/<uuid:upload_id>/', ExamScheduleUploadDetailView.as_view()),
    path('exam-schedule-uploads/<uuid:upload_id>/confirm/', ExamScheduleUploadConfirmView.as_view()),
]
