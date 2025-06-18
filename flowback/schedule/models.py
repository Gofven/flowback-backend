import datetime
import json

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models.signals import post_save, post_delete, pre_delete
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from rest_framework.exceptions import ValidationError

from flowback.common.models import BaseModel
from django.utils.translation import gettext_lazy as _


# Create your models here.
class Schedule(BaseModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

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
    meeting_link = models.URLField(null=True, blank=True)
    active = models.BooleanField(default=True)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    reminders = ArrayField(models.IntegerField(), size=10, null=True, blank=True)  # Max 10 reminders
    reminder_tasks = models.ManyToManyField(PeriodicTask)
    repeat_frequency = models.IntegerField(null=True, blank=True, choices=Frequency.choices)
    assignees = models.ManyToManyField('user.User')

    # Relating ScheduleEvent to other models
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def clean(self):
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date is greater than end date')

        if self.reminders:
            if list(set(self.reminders)) < self.reminders:  # TODO check if this works
                raise ValidationError("Reminders can't have duplicates")

    @classmethod
    def post_save(cls, instance, created, *args, **kwargs):
        # Offset start_date by the earliest reminder - 1 minute

        if not created:
            if instance.reminder_tasks.exists():
                instance.reminder_tasks.all().delete()

        if not instance.reminders:
            return

        for i in instance.reminders:
            start_date = instance.start_date - datetime.timedelta(seconds=i)
            repeat_frequency = instance.repeat_frequency

            data = None

            # TODO add reminders for one-off events, verify reminders don't intersect during repeat
            if repeat_frequency:  # Create scheduled notifications on repeat
                freq = instance.Frequency
                match repeat_frequency:
                    case freq.DAILY: data = dict(minute=start_date.minute,
                                                 hour=start_date.hour)

                    case freq.WEEKLY: data = dict(minute=start_date.minute,
                                                  hour=start_date.hour,
                                                  day_of_week=int(start_date.today().strftime('%w')))

                    case freq.MONTHLY: data = dict(minute=start_date.minute,
                                                   hour=start_date.hour,
                                                   day_of_month=start_date.day)

                    case freq.YEARLY: data = dict(minute=start_date.minute,
                                                  hour=start_date.hour,
                                                  day_of_month=start_date.day,
                                                  month_of_year=start_date.month)

                if data:
                    # TODO automatic purging of dangling CrontabSchedules
                    schedule = CrontabSchedule.objects.get_or_create(**data)
                    periodic_task = PeriodicTask.objects.create(name=f"schedule_event_{instance.id}_{i}",
                                                                task="schedule.tasks.event_notify",
                                                                kwargs=json.dumps(dict(event_id=instance.id)),
                                                                crontab=schedule[0])
                    periodic_task.save()

                    instance.reminder_tasks.add(periodic_task)
                    instance.save()

    @classmethod  # Delete reminders
    def pre_delete(cls, instance, *args, **kwargs):
        if instance.reminder_tasks.exists():
            instance.reminder_tasks.all().delete()

post_save.connect(ScheduleEvent.post_save, ScheduleEvent)
pre_delete.connect(ScheduleEvent.pre_delete, ScheduleEvent)


# TODO revise subscription
class ScheduleSubscription(BaseModel):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='schedule_subscription_schedule')
    target = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='schedule_subscription_target')

    def clean(self):
        if self.schedule == self.target:
            raise ValidationError('Schedule cannot be the same as the target')

    class Meta:
        unique_together = ('schedule', 'target')
