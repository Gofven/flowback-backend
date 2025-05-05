from datetime import timedelta, datetime
from inspect import getfullargspec

from django.db import models
from django.db.models import F, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
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
    tag = models.CharField(max_length=255, help_text='Tag of the notification')
    data = models.JSONField(null=True, blank=True)  # Suggested to store relevant data for user
    timestamp = models.DateTimeField(default=timezone.now)
    channel = models.ForeignKey('notification.NotificationChannel', on_delete=models.CASCADE)

    def clean(self):
        if self.tag not in self.channel.tags:
            raise ValidationError('Invalid tag, must be in channel tags')

    @classmethod
    def post_save(cls, instance, created, *args, **kwargs):
        """
        Creates Notification for users on save for the given tag
        """

        subscription_filters = dict()
        subscription_q_filters = []
        if hasattr(instance, 'subscription_filters'):
            subscription_filters = instance.subscription_filters

        if hasattr(instance, 'subscription_q_filters'):
            subscription_q_filters = instance.subscription_q_filters

        if created:
            subscribers = NotificationSubscription.objects.filter(*subscription_q_filters,
                                                                  channel=instance.channel,
                                                                  tags__contains=[instance.tag],
                                                                  **subscription_filters)

            notifications = [Notification(user=x.user, notification_object=instance) for x in subscribers]
            Notification.objects.bulk_create(notifications)


post_save.connect(NotificationObject.post_save, NotificationObject)


# Notification is created for every user subscribed to a channel,
# with a NotificationObject attached to it containing the data
class Notification(BaseModel):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    notification_object = models.ForeignKey("notification.NotificationObject", on_delete=models.CASCADE)
    read = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'notification_object')


# Notification Subscription allows users to subscribe to the NotificationChannel, to get Notifications for themselves
class NotificationSubscription(BaseModel):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    channel = models.ForeignKey('notification.NotificationChannel', on_delete=models.CASCADE)
    tags = ArrayField(models.CharField(max_length=255), help_text='Tags that user has subscribed to')

    def clean(self):
        if not all([tag in self.channel.tags for tag in self.tags]):
            raise ValidationError(f'Not all categories exists for {self.channel.name}. '
                                  f'Following options are available: {", ".join(self.channel.tags)}')

    class Meta:
        unique_together = ('user', 'channel')


# For any model using Notification, it is recommended to use post_save to create a NotificationChannel object
class NotificationChannel(BaseModel):
    Action = NotificationObject.Action

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
        tag_func_names = [tag_func_name for tag_func_name in dir(self.content_object) if
                          tag_func_name.startswith('notify_')]

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
    def name(self) -> str:
        return self.content_object.__name__.lower()

    def notify(self,
               action: NotificationObject.Action,
               message: str,
               tag: str,
               timestamp: datetime = None,
               data: dict = None,
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
        :param tag:
        :param timestamp: Timestamp when this notification becomes active. Defaults to timezone.now().
        :param data: Additional data to pass to the notification.
        :param user_filters: List of filters to pass onto the delivery of notifications.
        :param user_q_filters: List of Q filters to pass onto the delivery of notifications.
        """
        if getattr(self.content_object, 'notification_data', False):
            data = data or {}
            data = zip(data, self.content_object.notification_data)

        extra_fields = dict(timestamp=timestamp)  # Dict of fields that has defaults in NotificationObject model
        notification_object = NotificationObject(channel=self,
                                                 action=action,
                                                 message=message,
                                                 tag=tag,
                                                 data=data,
                                                 **{k: v for k, v in extra_fields.items() if v is not None})

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

    def shift(self,
              delta: int,
              **query_filters) -> None:
        """
        Shifts notifications using the delta (in seconds)
        :param delta: How much time to shift notifications (in seconds)
        :param query_filters: Filters to apply to the NotificationObject query.
        """
        filters = {key: val for key, val in query_filters.items() if val is not None}
        self.notificationobject_set.filter(**filters).update(timestamp=F('timestamp') + timedelta(seconds=delta))

    def __str__(self):
        return f"<NotificationChannel {self.id}> for {self.content_object.__str__()}"

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def subscribe(self, *, user, channel, tags: list[str]) -> NotificationSubscription | None:
        # Delete subscription if no categories are present
        if not tags:
            NotificationSubscription.objects.get(user=user, channel=channel).delete()
            return None

        subscription, created = NotificationSubscription.objects.update_or_create(user=user,
                                                                                  channel=channel,
                                                                                  defaults=dict(tags=tags))

        return subscription


def generate_notification_channel(sender, instance, created, *args, **kwargs):
    if created and issubclass(sender, NotifiableModel):
        NotificationChannel.objects.create(content_object=instance)


class NotifiableModel(models.Model):
    """
    A plugin for models, adding notification functionality to the model.
    To add tags, make 'notify_{tag_name}' functions within the class that calls
    on the models notification_channel.notify function.
    The fields for the function will be used for checks and documentation.
    """
    notification_channels = GenericRelation(NotificationChannel)

    @property
    def notification_channel(self) -> NotificationChannel:
        return self.notification_channels.first()

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        models.signals.post_save.connect(generate_notification_channel, sender=cls)
