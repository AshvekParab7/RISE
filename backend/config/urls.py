from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView
from apps.academics.views import CollegeClassViewSet, ExamViewSet, SemesterViewSet, SubjectViewSet, SyllabusViewSet, TopicViewSet
from apps.resources.views import ResourceViewSet
from apps.tasks.views import StudySessionViewSet, TaskViewSet

router = DefaultRouter()
router.register('semesters', SemesterViewSet, basename='semester')
router.register('subjects', SubjectViewSet, basename='subject')
router.register('topics', TopicViewSet, basename='topic')
router.register('syllabus', SyllabusViewSet, basename='syllabus')
router.register('exams', ExamViewSet, basename='exam')
router.register('college-timetable', CollegeClassViewSet, basename='college-class')
router.register('resources', ResourceViewSet, basename='resource')
router.register('tasks', TaskViewSet, basename='task')
router.register('study-sessions', StudySessionViewSet, basename='study-session')

def health(_request):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/integrations/', include('apps.integrations.urls')),
    path('api/intelligence/', include('apps.intelligence.urls')),
    path('api/ai/', include('apps.ai.urls')),
    path('api/smart-tutor/', include('apps.smart_tutor.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
