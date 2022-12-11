from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import NotificationChannel, NotificationObject, Notification, NotificationSubscription
from flowback.common.services import get_object


def notification_load_channel(*, action: str, category: str, sender_type: str, sender_id: int) -> NotificationChannel:
    channel = NotificationChannel.objects.get_or_create(action=action,
                                                        category=category,
                                                        sender_type=sender_type,
                                                        sender_id=sender_id)
    return channel


def notification_delete_channel(*, sender_type: str, sender_id: int, action: str = None, category: str = None) -> None:
    channels = NotificationChannel.objects.filter(sender_type=sender_type, sender_id=sender_id,
                                                  action=action, category=category).all()
    channels.delete()
    return


# tag (Action), sender_type (Name), sender_id (identifier)
# Notification subscription handled outside, notification management handled inside
def notification_create(*, action: str, category: str, sender_type: str, sender_id: int,
                        message: str, timestamp: int = None) -> NotificationObject:
    channel = notification_load_channel(action=action, category=category, sender_type=sender_type, sender_id=sender_id)
    notification_object = NotificationObject.objects.create(channel=channel,
                                                            message=message,
                                                            timestamp=timestamp)
    subscribers = NotificationSubscription.objects.filter(channel=channel).all()
    Notification.objects.bulk_create([Notification(user=subscriber.user,
                                                   notification_object=notification_object)
                                      for subscriber in subscribers])
    return notification_object


def notification_mark_read(*, fetched_by: int, notification_ids: list[int]) -> Notification:
    notification = get_object(Notification, user_id=fetched_by, id__in=notification_ids)
    notification.update(read=True)
    return notification


def notification_channel_subscribe(*,
                                   user_id: int,
                                   action: str,
                                   category: str,
                                   sender_type: str,
                                   sender_id: int) -> NotificationSubscription:
    channel = notification_load_channel(action=action, category=category, sender_type=sender_type, sender_id=sender_id)
    subscription = NotificationSubscription(user_id=user_id, channel=channel)
    subscription.full_clean()
    subscription.save()
    return subscription


def notification_channel_unsubscribe(*, user_id: int, action: str, category: str,
                                     sender_type: str, sender_id: int) -> None:
    channel = notification_load_channel(action=action, category=category, sender_type=sender_type, sender_id=sender_id)
    subscription = get_object(NotificationSubscription, user_id=user_id, channel=channel)
    subscription.delete()
    return


class NotificationManager:
    class Action:
        create = 'create'
        update = 'update'
        delete = 'delete'

    def __init__(self, sender_type: str, possible_categories: list[str]):
        self.sender_type = sender_type
        self.possible_categories = possible_categories

    def category_is_possible(self, category: str, validation: bool = False):
        if category not in self.possible_categories:
            message = f'Category {category} is not in possible_categories, ' \
                      f'choices are: {", ".join(self.possible_categories)}'
            if validation:
                raise ValidationError(message)
            else:
                raise Exception(message)

    def load_channel(self, *, sender_id: int, action: str, category: str):
        notification_load_channel(sender_type=self.sender_type, sender_id=sender_id, action=action, category=category)

    def delete_channel(self, *, sender_id: int, action: str = None, category: str = None):
        if category:
            self.category_is_possible(category)

        notification_delete_channel(sender_type=self.sender_type, sender_id=sender_id, action=action)

    def create(self, *, sender_id: int, action: str, category: str, message: str, timestamp: timezone.timezone = None):
        self.category_is_possible(action)

        notification_create(action=action, category=category, sender_type=self.sender_type, sender_id=sender_id,
                            message=message, timestamp=timestamp or timezone.now())

    def channel_subscribe(self, *, user_id: int, sender_id: int, action: str, category):
        self.category_is_possible(action, validation=True)

        notification_channel_subscribe(user_id=user_id, action=action, category=category, sender_type=self.sender_type,
                                       sender_id=sender_id)

    def channel_unsubscribe(self, *, user_id: int, sender_id: int, action: str, category):
        self.category_is_possible(action, validation=True)

        notification_channel_unsubscribe(user_id=user_id, action=action, category=category,
                                         sender_type=self.sender_type, sender_id=sender_id)
