from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone
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
    repeat_duration = models.IntegerField(null=True, blank=True, validators=[MaxValueValidator(86400)])  # In seconds
    repeat_task_id = models.IntegerField(null=True, blank=True)

    def clean(self):
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date is greater than end date')

        if self.repeat_duration:
            midnight = timezone.now().replace(hour=23, minute=59, second=59, microsecond=0)
            if self.repeat_duration > (midnight - self.start_date).seconds:
                raise ValidationError("Repeat duration cannot surpass the end of the day from the start date")


    def post_create(self, instance, created, update_fields, **kwargs):
        if created:
            pass  # TODO create celery task that repeats


class ScheduleSubscription(BaseModel):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='schedule_subscription_schedule')
    target = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='schedule_subscription_target')

    def clean(self):
        if self.schedule == self.target:
            raise ValidationError('Schedule cannot be the same as the target')

    class Meta:
        unique_together = ('schedule', 'target')
