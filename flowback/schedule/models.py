from django.db import models
from rest_framework.exceptions import ValidationError

from flowback.common.models import BaseModel


# Create your models here.
class Schedule(BaseModel):
    name = models.CharField()
    origin_name = models.CharField()
    origin_id = models.IntegerField()

    active = models.BooleanField(default=True)


class ScheduleEvent(BaseModel):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    title = models.TextField()
    description = models.TextField(null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(required=False)
    active = models.BooleanField(default=True)

    origin_name = models.CharField()
    origin_id = models.IntegerField()

    def clean(self):
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date is greater than end date')


class ScheduleSubscription(BaseModel):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    target = models.ForeignKey(Schedule, on_delete=models.CASCADE)

    def clean(self):
        if self.schedule == self.target:
            raise ValidationError('Schedule cannot be the same as the target')

    class Meta:
        unique_together = ('schedule', 'target')
