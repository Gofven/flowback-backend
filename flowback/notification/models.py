from datetime import timedelta, datetime

from django.db import models
from django.db.models import F, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from prometheus_client.decorator import getfullargspec
from rest_framework.exceptions import ValidationError

from flowback.common.models import BaseModel


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
    category = models.CharField(max_length=255, default='default', help_text='Category of the notification')
    data = models.JSONField(null=True, blank=True)  # Suggested to store relevant data for user
    timestamp = models.DateTimeField(default=timezone.now)
    channel = models.ForeignKey('notification.NotificationChannel', on_delete=models.CASCADE)

    notifications = models.ManyToManyField('notification.Notification')

    @classmethod
    def post_save(cls, instance, created, *args, **kwargs):
        """
        Creates Notification for users on save for the given category
        """

        subscription_filters = dict()
        subscription_q_filters = []
        if hasattr(instance, 'subscription_filters'):
            subscription_filters = instance.subscription_filters

        if hasattr(instance, 'subscription_q_filters'):
            subscription_q_filters = instance.subscription_q_filters

        if created:
            users = NotificationSubscription.objects.filter(*subscription_q_filters,
                                                            channel=instance.channel,
                                                            categories__in=[instance.category],
                                                            **subscription_filters).values('user')
            notifications = [Notification(user=x, notification_object=instance) for x in users]
            Notification.objects.bulk_create(notifications, ignore_conflicts=True)


# Notification is created for every user subscribed to a channel,
# with a NotificationObject attached to it containing the data
class Notification(BaseModel):
    user = models.OneToOneField('user.User', on_delete=models.CASCADE)
    notification_object = models.ForeignKey("notification.NotificationObject", on_delete=models.CASCADE)
    read = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'notification_object')


# Notification Subscription allows users to subscribe to the NotificationChannel, to get Notifications for themselves
class NotificationSubscription(BaseModel):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    channel = models.ForeignKey('notification.NotificationChannel', on_delete=models.CASCADE)
    categories = ArrayField(models.CharField(max_length=255))

    def clean(self):
        if not all([category in self.channel.categories for category in self.categories]):
            raise ValidationError(f'Not all categories exists for {self.channel.name}. '
                                  f'Following options are available: {", ".join(self.channel.categories)}')

    class Meta:
        unique_together = ('user', 'channel')


# For any model using Notification, it is recommended to use post_save to create a NotificationChannel object
class NotificationChannel(BaseModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    @property
    def tags(self) -> list | None:
        """
        A list containing notification tags.
        """
        return [tag.strip('notify_') for tag in dir(self.content_object) if tag.startswith('notify_')]

    def get_tag_fields(self, tag: str) -> list | None:
        """
        A list containing notification tag fields from the inheriting model.
        :param tag: Name of the notification tag
        :return:
        """

        # Get functions that starts with 'notify_'
        tag_func_names = [tag_func_name for tag_func_name in dir(self.content_object) if tag_func_name.startswith('notify_')]

        # Get attributes from the function related to tag and returns field names
        if f'notify_{tag}' in tag_func_names:
            excluded_fields = ['self', 'user_filters', 'user_q_filters']
            tag_fields = list(*getfullargspec(getattr(self.content_object, f'notify_{tag}'))[0])
            tag_fields = [tag_field for tag_field in tag_fields if tag_field not in excluded_fields]

            return tag_fields

        return None

    # Grabs the notification_data property from content_object (if any)
    @property
    def data(self) -> dict | None:
        notification_data = getattr(self.content_object, 'notification_data')
        return notification_data if notification_data else None

    @property
    def categories(self) -> list | None:
        notification_categories = getattr(self.content_object, 'notification_categories')
        return notification_categories if notification_categories else None

    @property
    def name(self) -> str:
        return self.content_object.__name__.lower()

    def notify(self,
               action: NotificationObject.Action,
               message: str,
               category: str,
               timestamp: datetime = None,
               data=None,
               user_filters: dict = None,
               user_q_filters: list[Q] = None) -> NotificationObject:
        """
        Creates a new notification.
        :param action: Check NotificationObject.Action for more information
        :param message: A text containing the message, if you wish to hyperlink a URL, do it in [text]() format.
         If you wish to add a URL, add the url beginning with `http://` or `https://` inside the ().
         If you wish to notify using the channel template, keep the () and leave it blank.
         If you wish to use a template from a different model, type in the exact model name inside the ().
         Missing template for the model name won't raise an error, but it will remove the URL.
        :param category:
        :param timestamp: Timestamp when this notification becomes active. Defaults to timezone.now().
        :param data: Additional data to pass to the notification. 'related_id' must be included for certain categories
        :param user_filters: List of filters to pass onto the delivery of notifications.
        :param user_q_filters: List of Q filters to pass onto the delivery of notifications.
        """
        notification_object = NotificationObject(channel=self,
                                                 action=action,
                                                 message=message,
                                                 category=category,
                                                 timestamp=timestamp,
                                                 data=data)

        notification_object.user_filters = user_filters or {}
        notification_object.user_q_filters = user_q_filters or []

        notification_object.full_clean()
        notification_object.save()

        return notification_object

    # TODO check if relevant, perhaps bulk delete is better
    def notification_object_delete(self,
                                   notification_object: NotificationObject | int):
        if isinstance(notification_object, NotificationObject):
            notification_object = notification_object.id

        NotificationObject.objects.get(channel_id=self.id, id=notification_object).delete()

    def notification_shift(self,
                           delta: int,
                           timestamp__lt: timezone = None,
                           timestamp__gt: timezone = None) -> None:
        """
        Shifts notifications using the delta (in seconds)
        :param timestamp__lt: Filters notifications based on timestamp
        :param timestamp__gt: Filters notifications based on timestamp
        :param delta: How much time to shift notifications (in seconds)
        """
        filters = {key: val for key, val in dict(timestamp__lt=timestamp__lt,
                                                 timestamp__gt=timestamp__gt) if val is not None}
        self.notificationobject_set.filter(filters).update(timestamp=F('timestamp') + timedelta(seconds=delta))

    def __str__(self):
        return f"<NotificationChannel {self.id}> for {self.content_object.__str__()}"

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


class NotifiableModel:
    """
    A plugin for models, adding notification functionality to the model.
    To add tags, make 'notify_{tag_name}' functions within the class that calls
    on the models notification_channel.notify function.
    The fields for the function will be used for checks and documentation.
    """
    notification_channel = GenericRelation(NotificationChannel)

    @property
    def notification_data(self):
        """
        dict containing data that is included in every NotificationObject's data field.
        """
        return None

    @receiver(post_save)
    def notification_channel_generator(self, instance, created, *args, **kwargs):
        if created:
            NotificationChannel.objects.create(content_object=instance)
