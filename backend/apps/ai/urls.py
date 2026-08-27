from django.urls import path
from .views import ConversationListView, PlannerView, ResourceStatusView, TestGenerateView, TestSubmitView, TutorView

urlpatterns = [
    path('tutor/', TutorView.as_view()),
    path('planner/', PlannerView.as_view()),
    path('conversations/', ConversationListView.as_view()),
    path('tests/generate/', TestGenerateView.as_view()),
    path('tests/<uuid:test_id>/submit/', TestSubmitView.as_view()),
    path('resources/<uuid:resource_id>/status/', ResourceStatusView.as_view()),
]
