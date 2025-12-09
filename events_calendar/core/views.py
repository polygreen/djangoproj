from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from calendar import monthcalendar, month_name
from .models import Event, Category, Profile
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

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


def get_events_for_month(year, month, events=None):
    if events is None:
        events = Event.objects.filter(owner=request.user)

    start_of_month = datetime(year, month, 1)
    end_of_month = (datetime(year + 1, 1, 1) - timedelta(days=1)) if month == 12 else (datetime(year, month + 1, 1) - timedelta(days=1))

    displayed = {}
    for event in events:
        dates = [event.start_date.date()]
        if event.repeat != 'none':
            freq_map = {'daily': DAILY, 'weekly': WEEKLY, 'monthly': MONTHLY, 'yearly': YEARLY}
            dtstart_utc = event.start_date.astimezone(timezone.utc).replace(tzinfo=None)
            until_utc = (end_of_month + timedelta(days=730)).astimezone(timezone.utc).replace(tzinfo=None)
            rule = rrule(freq_map[event.repeat], dtstart=dtstart_utc, until=until_utc)
            dates = [dt.date() for dt in rule 
                    if start_of_month.date() <= dt.date() <= end_of_month.date()]

        for d in dates:
            displayed.setdefault(d.day, []).append(event)
    return displayed

@login_required
def calendar_view(request, year=None, month=None):
    now = timezone.localtime()
    year = int(year) if year else now.year
    month = int(month) if month else now.month

    # Handle form submission (add event)
    if request.method == 'POST'and request.user.is_authenticated:
        title = request.POST.get('title')
        start_date_str = request.POST.get('start_date')
        category_id = request.POST.get('category') or None
        repeat = request.POST.get('repeat', 'none')

        if title and start_date_str:
            Event.objects.create(
                title=title,
                start_date=start_date_str,
                category_id=category_id,
                repeat=repeat,
                owner=request.user
            )
        return redirect('calendar_month', year=year, month=month)
    
    if request.method == 'POST':
        return redirect('login')
    
    # Category filter from URL
    category_id = request.GET.get('category')
    selected_category = None
    if category_id:
        try:
            selected_category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            pass

    # Get events (filtered if category selected)
    base_events = Event.objects.filter(owner=request.user)
    if selected_category:
        base_events = base_events.filter(category=selected_category)

    events_by_day = get_events_for_month(year, month, base_events)  # pass filtered events

    cal = monthcalendar(year, month)

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
        'categories': Category.objects.all(),
        'selected_category': selected_category,
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
        event.category_id = request.POST.get('category') or None
        event.repeat = request.POST.get('repeat', 'none')
        event.is_birthday = 'is_birthday' in request.POST
        event.save()
        return redirect('calendar_month', year=event.start_date.year, month=event.start_date.month)
    context = {
        'event': event,
        'categories': Category.objects.all(),       
        'repeat_choices': Event.REPEAT_CHOICES,     
    }
    return render(request, 'core/edit_event.html', context)
    

# Delete Event
def delete_event(request, event_id):
    event = Event.objects.get(id=event_id)
    year, month = event.start_date.year, event.start_date.month
    event.delete()
    return redirect('calendar_month', year=year, month=month)

# Event list
def event_list(request):
    # Get selected category from URL (e.g. ?category=3)
    category_id = request.GET.get('category')
    
    # Base queryset
    events = Event.objects.filter(owner=request.user).order_by('start_date')
    
    # Filter by category if selected
    selected_category = None
    if category_id:
        events = events.filter(category_id=category_id)
        try:
            selected_category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            pass

    context = {
        'events': events,
        'categories': Category.objects.all(),
        'selected_category': selected_category,
    }
    return render(request, 'core/event_list.html', context)

#category list
def category_list(request):
    if request.method == 'POST':
        name = request.POST['name'].strip()
        color = request.POST['color']
        if name:
            Category.objects.create(name=name, color=color)
        return redirect('category_list')

    categories = Category.objects.all().order_by('name')
    return render(request, 'core/category_list.html', {'categories': categories})

# Delete Category
@require_POST
def delete_category(request, pk):
    category = get_object_or_404(Category, id=pk)
    category_name = category.name
    category.delete()
    messages.success(request, f'Category "{category_name}" deleted.')
    return redirect('category_list')
   # return render(request, 'core/delete_category.html', {'category': category})

@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        request.user.profile.whatsapp_number = request.POST['whatsapp']
        request.user.profile.save()
        return redirect('profile')
    
    return render(request, 'core/profile.html', {'profile': profile})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            login(request, user)  # log them in immediately
            return redirect('calendar')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})