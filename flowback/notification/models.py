from django.db import models
from django.utils import timezone

from flowback.common.models import BaseModel
from flowback.user.models import User


class NotificationChannel(BaseModel):
    origin = models.CharField(max_length=255, help_text='Origin of the channel, preferably name of the parent model')


# NotificationObject is created containing data for each occurrence
class NotificationObject(BaseModel):
    class Action(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        UPDATED = 'UPDATED', 'Updated'
        DELETED = 'DELETED', 'Deleted'
        INFO = 'INFO', 'Info'
        WARNING = 'WARNING', 'Warning'
        ERROR = 'ERROR', 'Error'

    action = models.CharField(choices=Action.choices)
    message = models.TextField(max_length=2000)
    category = models.CharField(max_length=255, default='main', help_text='Category of the notification')
    data = models.JSONField(null=True, blank=True)  # Suggested to store relevant data for user
    timestamp = models.DateTimeField(default=timezone.now)
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)

    def post_save(self, created, *args, **kwargs):
        if created:
            users = NotificationSubscription.objects.filter(channel=self.channel).values('user')
            notifications = [Notification(user=x, notification_object=self) for x in users]
            Notification.objects.bulk_create(notifications, ignore_conflicts=True)



# Notification is created for every user subscribed to a channel,
# with a NotificationObject attached to it containing the data
class Notification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_object = models.ForeignKey("notification.NotificationObject", on_delete=models.CASCADE)
    read = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'notification_object')


# Notification Subscription allows users to subscribe to the NotificationChannel, to get Notifications for themselves
class NotificationSubscription(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'channel')



