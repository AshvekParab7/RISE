from django.urls import path
from .views import GoogleConnectionView, GoogleOAuthCallbackView, GoogleOAuthStartView
from .classroom_views import ClassroomStatusView, ClassroomSyncView
from .calendar_views import CalendarListView, CalendarStatusView, CalendarSyncView

urlpatterns = [
    path('google/', GoogleConnectionView.as_view()),
    path('google/start/', GoogleOAuthStartView.as_view()),
    path('google/callback/', GoogleOAuthCallbackView.as_view()),
    path('google/classroom/', ClassroomStatusView.as_view()),
    path('google/classroom/sync/', ClassroomSyncView.as_view()),
    path('google/calendar/', CalendarStatusView.as_view()),
    path('google/calendar/calendars/', CalendarListView.as_view()),
    path('google/calendar/sync/', CalendarSyncView.as_view()),
]
