from django.urls import path
from .views import DailyPlanView, NextActionView, PrioritiesView

urlpatterns = [
    path('priorities/', PrioritiesView.as_view()),
    path('next-action/', NextActionView.as_view()),
    path('daily-plan/', DailyPlanView.as_view()),
]
