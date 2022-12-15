from django.db import models
from django.utils import timezone

from flowback.common.models import BaseModel
from flowback.user.models import User


# Add get_or_create on every app startup for channels:
# https://stackoverflow.com/questions/6791911/execute-code-when-django-starts-once-only
class NotificationChannel(BaseModel):
    category = models.CharField(max_length=255)
    sender_type = models.CharField(max_length=255)
    sender_id = models.IntegerField()

    class Meta:
        unique_together = ('category', 'sender_type', 'sender_id')


class NotificationObject(BaseModel):
    related_id = models.IntegerField(null=True, blank=True)
    action = models.CharField(max_length=255)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)


class NotificationSubscription(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'channel')


class Notification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_object = models.ForeignKey(NotificationObject, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'notification_object')
