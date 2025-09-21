from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    ReportViewSet,
    
    # Individual Stats Cards APIs
    total_visitors_stat,
    active_visits_stat, 
    average_duration_stat,
    today_scheduled_stat,
    
    # Individual Charts APIs
    visitor_trends_chart,
    todays_activity_chart,
    todays_status_distribution,
    
    # Recent Activity API
    recent_activity_feed,
)

router = DefaultRouter()
router.register(r'', ReportViewSet)  # Changed from 'reports' to ''

urlpatterns = [
    # CRUD operations
    path('', include(router.urls)),
    
    # ===== INDIVIDUAL STATS CARDS APIS =====
    path('stats/total-visitors/', total_visitors_stat, name='total-visitors-stat'),
    path('stats/active-visits/', active_visits_stat, name='active-visits-stat'),
    path('stats/average-duration/', average_duration_stat, name='average-duration-stat'),
    path('stats/today-scheduled/', today_scheduled_stat, name='today-scheduled-stat'),
    
    # ===== INDIVIDUAL CHARTS APIS =====
    path('charts/visitor-trends/', visitor_trends_chart, name='visitor-trends-chart'),
    path('charts/todays-activity/', todays_activity_chart, name='todays-activity-chart'),
    path('charts/status-distribution/', todays_status_distribution, name='status-distribution-chart'),
    
    # ===== RECENT ACTIVITY API =====
    path('activity/recent/', recent_activity_feed, name='recent-activity-feed'),
]