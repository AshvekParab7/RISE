from django.urls import path
from .classroom_views import ClassroomStatusView, ClassroomSyncView

urlpatterns = [
    path('classroom/', ClassroomStatusView.as_view()),
    path('classroom/sync/', ClassroomSyncView.as_view()),
]
