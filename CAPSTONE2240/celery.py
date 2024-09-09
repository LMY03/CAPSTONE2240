import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CAPSTONE2240.settings')

app = Celery('CAPSTONE2240')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'delete-expired-requests': {
        'task': 'ticketing.tasks.delete_expired_requests',
        'schedule': crontab(minute=0, hour=0),
        # 'schedule': crontab(minute='*'),
    },
}