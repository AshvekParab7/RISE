from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from .services.recommendation_engine import build_context, build_daily_plan, build_next_action, calculate_priorities

class PrioritiesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        context = build_context(request.user)
        priorities = calculate_priorities(context)
        for item in priorities: item.setdefault('estimated_minutes', 45 if item.get('topic') else 30)
        status = build_daily_plan(context, int(request.query_params.get('available_minutes', 90)))['status']
        return Response({'generated_at': timezone.now(), 'overall_status': status, 'priorities': priorities})

class NextActionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request): return Response(build_next_action(build_context(request.user)))

class DailyPlanView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request): return Response(build_daily_plan(build_context(request.user), int(request.query_params.get('available_minutes', 90))))
