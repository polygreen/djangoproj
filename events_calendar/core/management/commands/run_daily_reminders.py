from django.core.management.base import BaseCommand
from core.whatsapp import send_daily_reminders, send_monthly_summary
from datetime import datetime

class Command(BaseCommand):
    help = 'Send WhatsApp daily reminders and monthly summary'

    def handle(self, *args, **options):
        send_daily_reminders()
        if datetime.now().day == 1:
            send_monthly_summary()
        self.stdout.write(self.style.SUCCESS('All reminders sent!'))