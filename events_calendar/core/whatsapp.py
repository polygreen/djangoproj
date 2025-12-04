from twilio.rest import Client
from django.conf import settings
from datetime import datetime, timedelta
from .models import Event

def send_whatsapp_reminder(phone_number, message):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        body=message,
        to=phone_number
    )
    return message.sid

def send_daily_reminders():
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    # 1. Day-before reminders (at 9 AM)
    events_tomorrow = Event.objects.filter(start_date__date=tomorrow)
    for event in events_tomorrow:
        msg = f"⏰ Reminder: Tomorrow!\n{event.title}\n📅 {event.start_date.strftime('%A, %B %d at %I:%M %p')}"
        if event.category:
            msg += f"\n🏷️ {event.category.name}"
        send_whatsapp_reminder(settings.YOUR_WHATSAPP_NUMBER, msg)

    # 2. Same-day reminders (at 8 AM)
    events_today = Event.objects.filter(start_date__date=today)
    for event in events_today:
        msg = f"🔔 Today!\n{event.title}\n🕐 {event.start_date.strftime('%I:%M %p')}"
        if event.category:
            msg += f"\n🏷️ {event.category.name}"
        send_whatsapp_reminder(settings.YOUR_WHATSAPP_NUMBER, msg)

def send_monthly_summary():
    today = datetime.now().date()
    if today.day != 1:
        return  # only run on 1st

    month = today.month
    year = today.year
    events = Event.objects.filter(
        start_date__year=year,
        start_date__month=month
    ).order_by('start_date')

    if not events:
        return

    msg = f"📅 Your {today.strftime('%B %Y')} Events:\n\n"
    for event in events:
        day = event.start_date.strftime("%A, %B %d")
        time = event.start_date.strftime("%I:%M %p")
        category = f" [{event.category.name}]" if event.category else ""
        msg += f"• {day} at {time}: {event.title}{category}\n"
    msg += "\nHave a great month! 🎉"

    send_whatsapp_reminder(settings.YOUR_WHATSAPP_NUMBER, msg)