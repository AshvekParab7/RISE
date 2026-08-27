from django.urls import path
from .views import CheckpointView, FinalChallengeView, LearningPathDetailView, LearningPathListView, LearningPathStatusView, LevelCompleteView, LevelDetailView, LevelListView, LevelStartView, NotesView, ResumeView, YouTubeLearningCreateView, YouTubeSearchView

urlpatterns = [
    path('youtube/', YouTubeLearningCreateView.as_view()),
    path('youtube/search/', YouTubeSearchView.as_view()),
    path('', LearningPathListView.as_view()),
    path('<uuid:path_id>/', LearningPathDetailView.as_view()),
    path('<uuid:path_id>/status/', LearningPathStatusView.as_view()),
    path('<uuid:path_id>/levels/', LevelListView.as_view()),
    path('<uuid:path_id>/levels/<uuid:level_id>/', LevelDetailView.as_view()),
    path('<uuid:path_id>/levels/<uuid:level_id>/start/', LevelStartView.as_view()),
    path('<uuid:path_id>/levels/<uuid:level_id>/complete/', LevelCompleteView.as_view()),
    path('<uuid:path_id>/checkpoint/', CheckpointView.as_view()),
    path('<uuid:path_id>/notes/', NotesView.as_view()),
    path('<uuid:path_id>/final-challenge/', FinalChallengeView.as_view()),
    path('<uuid:path_id>/resume/', ResumeView.as_view()),
]
