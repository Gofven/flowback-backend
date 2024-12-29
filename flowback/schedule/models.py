import datetime
import json

from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from rest_framework.exceptions import ValidationError

from flowback.common.models import BaseModel
from django.utils.translation import gettext_lazy as _


# Create your models here.
class Schedule(BaseModel):
    name = models.TextField()
    origin_name = models.CharField(max_length=255)
    origin_id = models.IntegerField()

    active = models.BooleanField(default=True)


class ScheduleEvent(BaseModel):
    class Frequency(models.IntegerChoices):
        DAILY = 1, _("Daily")
        WEEKLY = 2, _("Weekly")
        MONTHLY = 3, _("Monthly")  # If event start_date day is 29 or higher, skip months that has these dates
        YEARLY = 4, _("Yearly")

    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    title = models.TextField()
    description = models.TextField(null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    work_group = models.ForeignKey('group.WorkGroup', on_delete=models.CASCADE, null=True, blank=True)
    assignees = models.ManyToManyField('group.GroupUser')
    meeting_link = models.URLField(null=True, blank=True)

    origin_name = models.CharField(max_length=255)
    origin_id = models.IntegerField()

    repeat_frequency = models.IntegerField(null=True, blank=True, choices=Frequency.choices)
    repeat_task = models.ForeignKey(PeriodicTask, on_delete=models.CASCADE, null=True, blank=True)
    repeat_next_run = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date is greater than end date')

    @classmethod
    def post_save(cls, instance, created, *args, **kwargs):
        start_date = instance.start_date - datetime.timedelta(hours=2)  # Offset start_date by 2 hours

        if created:
            repeat_frequency = instance.repeat_frequency

            if repeat_frequency:  # Create scheduled notifications on repeat
                freq = instance.Frequency
                if repeat_frequency == freq.DAILY:
                    schedule = CrontabSchedule.objects.get_or_create(minute=start_date.minute,
                                                                     hour=start_date.hour)

                elif repeat_frequency == freq.WEEKLY:
                    schedule = CrontabSchedule.objects.get_or_create(minute=start_date.minute,
                                                                     hour=start_date.hour,
                                                                     day_of_week=int(start_date.today().strftime('%w')))

                elif repeat_frequency == freq.MONTHLY:
                    schedule = CrontabSchedule.objects.get_or_create(minute=start_date.minute,
                                                                     hour=start_date.hour,
                                                                     day_of_month=start_date.day)

                elif repeat_frequency == freq.YEARLY:
                    schedule = CrontabSchedule.objects.get_or_create(minute=start_date.minute,
                                                                     hour=start_date.hour,
                                                                     day_of_month=start_date.day,
                                                                     month_of_year=start_date.month)

                else:
                    return

                periodic_task = PeriodicTask.objects.create(name="Schedule Event",
                                                            task="schedule.tasks.event_notify",
                                                            kwargs=json.dumps(dict(event_id=instance.id,
                                                                                   reminders=[0, 7200])),
                                                            crontab=schedule)
                periodic_task.save()

                instance.repeat_task = periodic_task
                instance.save()

    @classmethod
    def post_delete(cls, instance, *args, **kwargs):
        if instance.periodic_task:
            instance.periodic_task.delete()

post_save.connect(ScheduleEvent.post_save, ScheduleEvent)
post_delete.connect(ScheduleEvent.post_delete, ScheduleEvent)


class ScheduleSubscription(BaseModel):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='schedule_subscription_schedule')
    target = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='schedule_subscription_target')

    def clean(self):
        if self.schedule == self.target:
            raise ValidationError('Schedule cannot be the same as the target')

    class Meta:
        unique_together = ('schedule', 'target')
