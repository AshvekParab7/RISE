from django.urls import path
from .views import ConversationListView, PlannerConversationDetailView, PlannerConversationListView, PlannerConversationMessageView, PlannerView, ResourceStatusView, TestGenerateView, TestSubmitView, TutorView

urlpatterns = [
    path('tutor/', TutorView.as_view()),
    path('planner/', PlannerView.as_view()),
    path('planner/conversations/', PlannerConversationListView.as_view()),
    path('planner/conversations/<uuid:conversation_id>/', PlannerConversationDetailView.as_view()),
    path('planner/conversations/<uuid:conversation_id>/messages/', PlannerConversationMessageView.as_view()),
    path('conversations/', ConversationListView.as_view()),
    path('tests/generate/', TestGenerateView.as_view()),
    path('tests/<uuid:test_id>/submit/', TestSubmitView.as_view()),
    path('resources/<uuid:resource_id>/status/', ResourceStatusView.as_view()),
]
