from rest_framework import viewsets, permissions
from .models import Report
from .serializers import ReportSerializer
 
# views.py - Separate APIs for each dashboard component
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import timedelta, datetime, date
from collections import defaultdict
from .models import Report
from invites.models import Invite
from visitors.models import Visitor

# =====================
# 1. TOP STATS CARDS - Individual APIs
# =====================

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related('visitor', 'invite').all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def total_visitors_stat(request):
    """API for Total Visitors card"""
    try:
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Total visitors count
        total_count = Report.objects.count()
        
        # Today's visitors
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        today_end = today_start + timedelta(days=1)
        today_visitors = Report.objects.filter(
            check_in__gte=today_start,
            check_in__lt=today_end
        ).count()
        
        # Yesterday's visitors for growth calculation
        yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
        yesterday_end = yesterday_start + timedelta(days=1)
        yesterday_visitors = Report.objects.filter(
            check_in__gte=yesterday_start,
            check_in__lt=yesterday_end
        ).count()
        
        # Calculate growth
        growth = calculate_growth_percentage(today_visitors, yesterday_visitors)
        
        return Response({
            'success': True,
            'data': {
                'total_visitors': total_count,
                'today_visitors': today_visitors,
                'yesterday_visitors': yesterday_visitors,
                'growth': growth,
                'label': 'Total Visitors',
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': {'total_visitors': 0, 'growth': '0%'}
        }, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def active_visits_stat(request):
    try:
        active_qs = Report.objects.filter(
            check_in__isnull=False,
            check_out__isnull=True
        )
        active_count = active_qs.count()

        limit = int(request.GET.get('limit', 5))
        active_visitors = active_qs.select_related('visitor', 'invite').order_by('-check_in')[:limit]

        active_details = []
        for report in active_visitors:
            visitor_name = report.visitor.name if report.visitor else (
                report.invite.visitor_name if report.invite else "Unknown"
            )
            active_details.append({
                'name': visitor_name,
                'check_in_time': report.check_in.isoformat(),
                'duration': get_time_since(report.check_in)
            })

        return Response({
            'success': True,
            'data': {
                'active_visits': active_count,
                'active_visitors': active_details,
                'label': 'Active Visits',
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': {'active_visits': 0, 'active_visitors': []}
        }, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def average_duration_stat(request):
    """API for Average Duration card"""
    try:
        # Get all completed visits
        completed_visits = Report.objects.filter(
            check_in__isnull=False,
            check_out__isnull=False
        )
        
        if not completed_visits.exists():
            return Response({
                'success': True,
                'data': {
                    'average_duration': '0m',
                    'total_minutes': 0,
                    'completed_visits_count': 0,
                    'label': 'Avg. Duration',
                    'timestamp': timezone.now().isoformat()
                }
            })
        
        total_duration_minutes = 0
        duration_details = []
        
        for report in completed_visits:
            duration = report.check_out - report.check_in
            duration_minutes = duration.total_seconds() / 60
            total_duration_minutes += duration_minutes
            
            # Store individual durations for analysis
            duration_details.append({
                'visitor_name': report.visitor.name if report.visitor else (
                    report.invite.visitor_name if report.invite else "Unknown"
                ),
                'duration_minutes': round(duration_minutes, 2),
                'check_in': report.check_in.isoformat(),
                'check_out': report.check_out.isoformat()
            })
        
        avg_minutes = total_duration_minutes / len(duration_details)
        avg_hours = int(avg_minutes // 60)
        remaining_minutes = int(avg_minutes % 60)
        
        formatted_duration = f"{avg_hours}h {remaining_minutes}m" if avg_hours > 0 else f"{remaining_minutes}m"
        
        return Response({
            'success': True,
            'data': {
                'average_duration': formatted_duration,
                'total_minutes': round(avg_minutes, 2),
                'hours': avg_hours,
                'minutes': remaining_minutes,
                'completed_visits_count': len(duration_details),
                'label': 'Avg. Duration',
                'recent_durations': duration_details[-5:],  # Last 5 for analysis
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': {'average_duration': '0m', 'total_minutes': 0}
        }, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def today_scheduled_stat(request):
    """API for Today Scheduled card"""
    try:
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        today_end = today_start + timedelta(days=1)
        
        yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
        yesterday_end = yesterday_start + timedelta(days=1)
        
        # Today's scheduled invites
        today_scheduled = Invite.objects.filter(
            created_at__gte=today_start,
            created_at__lt=today_end
        ).count()
        
        # Yesterday's scheduled for growth
        yesterday_scheduled = Invite.objects.filter(
            created_at__gte=yesterday_start,
            created_at__lt=yesterday_end
        ).count()
        
        # Get recent scheduled invites
        recent_invites = Invite.objects.filter(
            created_at__gte=today_start,
            created_at__lt=today_end
        ).order_by('-created_at')[:5]
        
        recent_details = []
        for invite in recent_invites:
            recent_details.append({
                'visitor_name': invite.visitor_name,
                'visitor_email': invite.visitor_email if hasattr(invite, 'visitor_email') else None,
                'purpose': invite.purpose if hasattr(invite, 'purpose') else None,
                'created_time': invite.created_at.isoformat(),
                'status': invite.status if hasattr(invite, 'status') else 'scheduled'
            })
        
        growth = calculate_growth_percentage(today_scheduled, yesterday_scheduled)
        
        return Response({
            'success': True,
            'data': {
                'today_scheduled': today_scheduled,
                'yesterday_scheduled': yesterday_scheduled,
                'growth': growth,
                'recent_invites': recent_details,
                'label': 'Today Scheduled',
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': {'today_scheduled': 0, 'growth': '0%'}
        }, status=500)

# =====================
# 2. CHARTS - Individual APIs
# =====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def visitor_trends_chart(request):
    """API for Visitor Trends Chart"""
    try:
        days = int(request.GET.get('days', 7))  # Default 7 days
        today = timezone.now().date()
        
        visitor_data = []
        invite_data = []
        
        for i in range(days-1, -1, -1):
            day = today - timedelta(days=i)
            day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
            day_end = day_start + timedelta(days=1)
            
            # Visitors count for this day
            visitors_count = Report.objects.filter(
                check_in__gte=day_start,
                check_in__lt=day_end
            ).count()
            
            # Invites count for this day
            invites_count = Invite.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            ).count()
            
            visitor_data.append({
                'date': day.strftime('%Y-%m-%d'),
                'display_date': day.strftime('%m/%d'),
                'day_name': day.strftime('%a'),
                'visitors': visitors_count
            })
            
            invite_data.append({
                'date': day.strftime('%Y-%m-%d'),
                'display_date': day.strftime('%m/%d'),
                'day_name': day.strftime('%a'),
                'invites': invites_count
            })
        
        # Calculate trends
        total_visitors = sum(item['visitors'] for item in visitor_data)
        total_invites = sum(item['invites'] for item in invite_data)
        
        return Response({
            'success': True,
            'data': {
                'visitor_trends': visitor_data,
                'invite_trends': invite_data,
                'summary': {
                    'total_visitors': total_visitors,
                    'total_invites': total_invites,
                    'days_count': days,
                    'avg_daily_visitors': round(total_visitors / days, 1),
                    'avg_daily_invites': round(total_invites / days, 1)
                },
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': {'visitor_trends': [], 'invite_trends': []}
        }, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def todays_activity_chart(request):
    """API for Today's Activity Chart (Hourly breakdown)"""
    try:
        today = timezone.now().date()
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        current_hour = timezone.now().hour
        
        hourly_data = []
        peak_activity = 0
        peak_hour = None
        
        for hour in range(24):
            hour_start = today_start.replace(hour=hour)
            hour_end = hour_start + timedelta(hours=1)
            
            # Count check-ins for this hour
            activity_count = Report.objects.filter(
                check_in__gte=hour_start,
                check_in__lt=hour_end
            ).count()
            
            # Track peak hour
            if activity_count > peak_activity:
                peak_activity = activity_count
                peak_hour = f"{hour:02d}:00"
            
            hourly_data.append({
                'hour': hour,
                'hour_display': f"{hour:02d}:00",
                'activity': activity_count,
                'is_current_hour': hour == current_hour,
                'is_peak': activity_count == peak_activity if peak_activity > 0 else False
            })
        
        total_activity = sum(item['activity'] for item in hourly_data)
        
        return Response({
            'success': True,
            'data': {
                'hourly_activity': hourly_data,
                'summary': {
                    'total_activity': total_activity,
                    'peak_hour': peak_hour,
                    'peak_activity': peak_activity,
                    'current_hour': current_hour,
                    'avg_hourly_activity': round(total_activity / 24, 1)
                },
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': {'hourly_activity': []}
        }, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def todays_status_distribution(request):
    """API for Today's Status Pie Chart"""
    try:
        today = timezone.now().date()
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        today_end = today_start + timedelta(days=1)
        
        # Checked In (active visits today)
        checked_in = Report.objects.filter(
            check_in__gte=today_start,
            check_in__lt=today_end,
            check_out__isnull=True
        ).count()
        
        # Completed visits today
        completed = Report.objects.filter(
            check_in__gte=today_start,
            check_in__lt=today_end,
            check_out__isnull=False
        ).count()
        
        # Scheduled for today
        scheduled = Invite.objects.filter(
            created_at__gte=today_start,
            created_at__lt=today_end
        ).count()
        
        total = checked_in + completed + scheduled
        
        distribution_data = [
            {
                'status': 'checked_in',
                'label': 'Checked In',
                'count': checked_in,
                'percentage': round((checked_in / total * 100) if total > 0 else 0, 1),
                'color': '#3B82F6'  # Blue
            },
            {
                'status': 'completed', 
                'label': 'Completed',
                'count': completed,
                'percentage': round((completed / total * 100) if total > 0 else 0, 1),
                'color': '#10B981'  # Green
            },
            {
                'status': 'scheduled',
                'label': 'Scheduled', 
                'count': scheduled,
                'percentage': round((scheduled / total * 100) if total > 0 else 0, 1),
                'color': '#F59E0B'  # Yellow
            }
        ]
        
        return Response({
            'success': True,
            'data': {
                'distribution': distribution_data,
                'summary': {
                    'total_today': total,
                    'checked_in': checked_in,
                    'completed': completed,
                    'scheduled': scheduled
                },
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': {'distribution': []}
        }, status=500)

# =====================
# 3. RECENT ACTIVITY - Individual API
# =====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def recent_activity_feed(request):
    """API for Recent Activity feed"""
    try:
        limit = int(request.GET.get('limit', 10))  # Default 10 recent activities
        
        # Get recent reports ordered by latest activity
        recent_reports = Report.objects.select_related('visitor', 'invite').filter(
            check_in__isnull=False
        ).order_by('-check_in')[:limit]
        
        activities = []
        for report in recent_reports:
            # Determine visitor name
            visitor_name = "Unknown Visitor"
            if report.visitor:
                visitor_name = report.visitor.name
            elif report.invite:
                visitor_name = report.invite.visitor_name
            
            # Determine status and action
            if report.check_out:
                status = "Checked out"
                action_type = "checkout"
                activity_time = report.check_out
                duration = report.check_out - report.check_in
                duration_text = f"Duration: {int(duration.total_seconds() // 3600)}h {int((duration.total_seconds() % 3600) // 60)}m"
            else:
                status = "Checked in"
                action_type = "checkin"
                activity_time = report.check_in
                duration_text = f"Active for: {get_time_since(report.check_in)}"
            
            activities.append({
                'id': report.id,
                'visitor_name': visitor_name,
                'status': status,
                'action_type': action_type,
                'time_ago': get_time_ago(activity_time),
                'exact_time': activity_time.isoformat(),
                'duration_info': duration_text,
                'visitor_type': 'registered' if report.visitor else 'invited'
            })
        
        return Response({
            'success': True,
            'data': {
                'recent_activities': activities,
                'total_shown': len(activities),
                'limit': limit,
                'timestamp': timezone.now().isoformat()
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': {'recent_activities': []}
        }, status=500)

# =====================
# UTILITY FUNCTIONS
# =====================

def calculate_growth_percentage(current, previous):
    """Calculate growth percentage between two values"""
    if previous == 0:
        return '+100%' if current > 0 else '0%'
    
    growth = ((current - previous) / previous) * 100
    if growth > 0:
        return f'+{growth:.1f}%'
    elif growth < 0:
        return f'{growth:.1f}%'
    else:
        return '0%'

def get_time_ago(datetime_obj):
    """Get human readable time ago string"""
    now = timezone.now()
    diff = now - datetime_obj
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def get_time_since(datetime_obj):
    """Get time since a datetime (for active duration)"""
    now = timezone.now()
    diff = now - datetime_obj
    
    if diff.days > 0:
        return f"{diff.days} days"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes"
    else:
        return "< 1 minute"