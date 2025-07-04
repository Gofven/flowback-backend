import datetime
import json

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.signals import post_save, post_delete, pre_delete
from django_celery_beat.models import PeriodicTask, CrontabSchedule, ClockedSchedule
from rest_framework.exceptions import ValidationError

from flowback.common.models import BaseModel
from django.utils.translation import gettext_lazy as _

from flowback.notification.models import NotifiableModel


# TODO Schedules should have user-defined tags as categories.
#


# Create your models here.
class Schedule(BaseModel, NotifiableModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    active = models.BooleanField(default=True)

    def subscribe(self, user):
        ScheduleSubscription.objects.get_or_create(user=user, schedule=self)

    def unsubscribe(self, user):
        ScheduleSubscription.objects.filter(user=user, schedule=self).delete()

    def notification_data(self) -> dict | None:
        return dict(id=self.id,
                    source_model=self.content_object.__class__.__name__.lower(),
                    source_id=self.object_id)

    def notify_schedule_event(self,
                              title: str,
                              action: str,
                              schedule_event_id: int,
                              message: str):
        data = locals()
        data.pop('self')

        return self.notification_channel.notify(**data)

    def notify_schedule_assignment(self,
                                   title: str,
                                   action: str,
                                   schedule_event_id: int,
                                   message: str,
                                   user_ids: list[int] | int | None = None):
        data = locals()
        data.pop('self')

        if user_ids:
            if isinstance(user_ids, int):
                user_ids = [user_ids]

            data.pop('user_ids')
            data['subscription_filters'] = {'user_id__in': user_ids}

        return self.notification_channel.notify(**data)


# A list of tags for the schedule, also contains default reminders for events
class ScheduleTag(BaseModel):
    pass


class ScheduleEvent(BaseModel, NotifiableModel):
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
    reminders = ArrayField(models.DateTimeField(), size=10, null=True, blank=True)  # Max 10 reminders
    reminder_tasks = models.ManyToManyField(PeriodicTask)
    repeat_frequency = models.IntegerField(null=True, blank=True, choices=Frequency.choices)
    assignees = models.ManyToManyField('user.User')

    # Relating ScheduleEvent to other models
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def notification_data(self) -> dict | None:
        return dict(id=self.id,
                    source_model=self.content_object.__class__.__name__.lower(),
                    source_id=self.object_id,
                    title=self.title)

    def notify_schedule_event(self,
                              action: str,
                              message: str):
        """Notifies when a schedule event reminders, as well as when it starts"""
        data = locals()
        data.pop('self')

        return self.notification_channel.notify(**data)


    # TODO get upcoming & previous start/end dates


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

        freq = instance.Frequency

        # Verify all reminders are valid
        failed_checks = []
        for i in instance.reminders:
            passed_check = True

            # Monthly and yearly intersections may vary, so instead it's written to allow for such intersections
            match instance.repeat_frequency:
                case freq.DAILY: passed_check = (instance.start_date - i).seconds <= 86399
                case freq.WEEKLY: passed_check = (instance.start_date - i).seconds <= 604799
                case freq.MONTHLY: passed_check = (instance.start_date - i).seconds <= 2678399
                case freq.YEARLY: passed_check = (instance.start_date - i).seconds <= 31556927

            # Check if failed or reminder occurs after the start date
            if not passed_check or (instance.start_date - i).seconds <= 0:
                failed_checks.append(i)

        if failed_checks:
            raise ValidationError(f"Folllowing reminders are invalid: {', '.join(str(failed_checks))}")


        for i in instance.reminders:
            repeat_frequency = instance.repeat_frequency

            data = None

            if not repeat_frequency:
                schedule = ClockedSchedule.objects.create(clocked_time=i)
                periodic_task = PeriodicTask.objects.create(name=f"schedule_event_{instance.id}_{i}",
                                                            task="schedule.tasks.event_notify",
                                                            one_off=True,
                                                            kwargs=json.dumps(dict(event_id=instance.id)),
                                                            clocked=schedule)

                instance.reminder_tasks.add(periodic_task)
                instance.save()

            elif repeat_frequency:  # Create scheduled notifications on repeat
                match repeat_frequency:
                    case freq.DAILY: data = dict(minute=i.minute,
                                                 hour=i.hour)

                    case freq.WEEKLY: data = dict(minute=i.minute,
                                                  hour=i.hour,
                                                  day_of_week=int(i.today().strftime('%w')))

                    case freq.MONTHLY: data = dict(minute=i.minute,
                                                   hour=i.hour,
                                                   day_of_month=i.day)

                    case freq.YEARLY: data = dict(minute=i.minute,
                                                  hour=i.hour,
                                                  day_of_month=i.day,
                                                  month_of_year=i.month)

                if data:  # Create a repeating cron schedule for the event task
                    # TODO automatic purging of dangling CrontabSchedules
                    schedule = CrontabSchedule.objects.get_or_create(**data)
                    periodic_task = PeriodicTask.objects.create(name=f"schedule_event_{instance.id}_{i}",
                                                                task="schedule.tasks.event_notify",
                                                                kwargs=json.dumps(dict(event_id=instance.id)),
                                                                crontab=schedule[0])

                    instance.reminder_tasks.add(periodic_task)
                    instance.save()

    @classmethod  # Delete reminders
    def pre_delete(cls, instance, *args, **kwargs):
        if instance.reminder_tasks.exists():
            instance.reminder_tasks.all().delete()

post_save.connect(ScheduleEvent.post_save, ScheduleEvent)
pre_delete.connect(ScheduleEvent.pre_delete, ScheduleEvent)


class ScheduleSubscription(BaseModel):
    user = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'schedule'], name='unique_schedule_subscription')]

    @classmethod
    def post_delete(cls, instance, *args, **kwargs):
        # Unsubscribe all notification channels from Schedule and ScheduleEvents
        instance.schedule.notification_channel.unsubscribe_all(instance.user)


post_delete.connect(ScheduleSubscription.post_delete, ScheduleSubscription)


# A link between tag and subscription to override the usual reminders given to each tag
class ScheduleSubscriptionTagReminders(BaseModel):
    tag = models.ForeignKey(ScheduleTag, on_delete=models.CASCADE)
    subscription = models.ForeignKey(ScheduleSubscription, on_delete=models.CASCADE)


def generate_schedule(sender, instance, created, *args, **kwargs):
    if created:
        Schedule.objects.create(content_object=instance)


class SchedulePluginModel(models.Model):
    """
    A plugin for models, adding schedule functionality to the model.
    """
    related_schedules = GenericRelation(Schedule, on_delete=models.CASCADE)

    @property
    def schedule(self) -> Schedule:
        return self.related_schedules.first()

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        models.signals.post_save.connect(generate_schedule, sender=cls)
