from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from datetime import datetime
from calendar import monthcalendar, month_name
from .models import Event
from django.utils import timezone

def _get_count(session):
    """
    Helper: read the counter from the session.
    If missing, default to 0.
    """
    return session.get("count", 0)
def _set_count(session, value):
    """
    Helper: write the counter to the session.
    """
    session["count"] = value
@require_http_methods(["GET", "HEAD"])
def home(request):
    """
    Purpose: Show the current count.
    Why GET only: Viewing should not change state (safe/idempotent).
    """
    count = _get_count(request.session)
    return render(request, "core/home.html", {"count": count})
@require_http_methods(["GET", "HEAD"])
def about(request):
    """
    Purpose: Simple second page to demonstrate routing and navigation.
    """
    return render(request, "core/about.html")
@require_http_methods(["POST"])
def increment(request):
    """
    Purpose: Handle the increment action.
    Why POST: It changes server state, so it must not be a GET.
    Workflow: Read -> modify -> save -> redirect (PRG pattern).
    """
    current = _get_count(request.session)
    _set_count(request.session, current + 1)
    return redirect("home") # Post-Redirect-Get avoids double submits on refresh
def calendar_view(request, year=None, month=None):
    now = datetime.now()
    year  = int(year)  if year  else now.year
    month = int(month) if month else now.month

    # Build a 6×7 grid (some months need 6 rows)
    cal = monthcalendar(year, month)

    # Gather events for this month
    events = Event.objects.filter(
        start_date__year=year,
        start_date__month=month
    )

    # Group by day
    events_by_day = {}
    for e in events:
        day = e.start_date.day
        events_by_day.setdefault(day, []).append(e)

    context = {
        'year': year,
        'month': month,
        'month_name': month_name[month],
        'calendar': cal,
        'events_by_day': events_by_day,
        'prev_year': year - (1 if month == 1 else 0),
        'prev_month': 12 if month == 1 else month - 1,
        'next_year': year + (1 if month == 12 else 0),
        'next_month': 1 if month == 12 else month + 1,
    }
    return render(request, 'core/calendar.html', context)

def calendar_view(request, year=None, month=None):
    now = timezone.localtime()
    year  = int(year)  if year  else now.year
    month = int(month) if month else now.month

    # Handle form submission
    if request.method == 'POST':
        title = request.POST.get('title')
        start_date = request.POST.get('start_date')
        if title and start_date:
            Event.objects.create(
                title=title,
                start_date=start_date
            )
        return redirect('calendar_month', year=year, month=month)

    # Build calendar
    cal = monthcalendar(year, month)
    events = Event.objects.filter(
        start_date__year=year,
        start_date__month=month
    )
    events_by_day = {}
    for e in events:
        day = e.start_date.day
        events_by_day.setdefault(day, []).append(e)

    context = {
        'year': year,
        'month': month,
        'month_name': month_name[month],
        'calendar': cal,
        'events_by_day': events_by_day,
        'prev_year': year - (1 if month == 1 else 0),
        'prev_month': 12 if month == 1 else month - 1,
        'next_year': year + (1 if month == 12 else 0),
        'next_month': 1 if month == 12 else month + 1,
        'today_day': now.day,
        'today_month': now.month,
        'today_year': now.year,
    }
    return render(request, 'core/calendar.html', context)

# Edit Event
def edit_event(request, event_id):
    event = Event.objects.get(id=event_id)
    
    if request.method == 'POST':
        event.title = request.POST['title']
        event.description = request.POST.get('description', '')

        # Parse the string into a datetime object
        start_date_str = request.POST['start_date']
        try:
            event.start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            # Optional: make it timezone-aware
            event.start_date = timezone.make_aware(event.start_date)
        except ValueError:
            # If format is wrong, fallback or show error
            pass

        event.save()
        return redirect('calendar_month', year=event.start_date.year, month=event.start_date.month)
    
    return render(request, 'core/edit_event.html', {'event': event})

# Delete Event
def delete_event(request, event_id):
    event = Event.objects.get(id=event_id)
    year, month = event.start_date.year, event.start_date.month
    event.delete()
    return redirect('calendar_month', year=year, month=month)

# Event list
def event_list(request):
    events = Event.objects.all().order_by('start_date')
    return render(request, 'core/event_list.html', {'events': events})