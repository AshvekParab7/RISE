from django.urls import path

from .views import ConversationListView, FlashcardView, MCQView, TutorView

urlpatterns = [
    path('tutor/', TutorView.as_view()),
    path('conversations/', ConversationListView.as_view()),
    path('flashcards/', FlashcardView.as_view()),
    path('mcqs/', MCQView.as_view()),
]
