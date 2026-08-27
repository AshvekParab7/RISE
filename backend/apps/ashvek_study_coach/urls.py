from django.urls import path
from .views import AnswerView, CompleteSessionView, EvaluateView, PracticeView, ReportView, RevisionView, SessionDetailView, SessionListCreateView, TeachView, WeaknessView

urlpatterns = [
    path('sessions/', SessionListCreateView.as_view()),
    path('sessions/<uuid:session_id>/', SessionDetailView.as_view()),
    path('sessions/<uuid:session_id>/complete/', CompleteSessionView.as_view()),
    path('teach/', TeachView.as_view()),
    path('answer/', AnswerView.as_view()),
    path('evaluate/', EvaluateView.as_view()),
    path('practice/', PracticeView.as_view()),
    path('revision/', RevisionView.as_view()),
    path('session/<uuid:session_id>/report/', ReportView.as_view()),
    path('session/<uuid:session_id>/weaknesses/', WeaknessView.as_view()),
]
