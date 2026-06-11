from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Create or update periodic Celery tasks required by n-feed."

    def handle(self, *args, **options):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="3",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
            timezone="UTC",
        )
        PeriodicTask.objects.update_or_create(
            name="cleanup old notifications",
            defaults={
                "crontab": schedule,
                "task": "notifications.tasks.cleanup_old_notifications",
                "kwargs": '{"days": 30}',
                "enabled": True,
            },
        )
        PeriodicTask.objects.update_or_create(
            name="cleanup orphan media",
            defaults={
                "crontab": schedule,
                "task": "tweets.tasks.cleanup_orphan_media_task",
                "enabled": True,
            },
        )
        self.stdout.write(self.style.SUCCESS("Configured periodic Celery tasks."))
