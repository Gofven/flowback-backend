from .models import NotificationChannel, NotificationObject, Notification, NotificationSubscription
from flowback.common.services import get_object


def notification_create_channel(*, action: str, sender_type: str, sender_id: int,
                                   title: str, description: str) -> NotificationChannel:
    channel = NotificationChannel(action=action,
                                  sender_type=sender_type,
                                  sender_id=sender_id,
                                  title=title,
                                  description=description)
    channel.full_clean()
    channel.save()
    return channel


def notification_delete_channel(*, action: str, sender_type: str, sender_id: int) -> None:
    channel = get_object(NotificationChannel, action=action, sender_type=sender_type, sender_id=sender_id)
    channel.delete()
    return


# tag (Action), sender_type (Name), sender_id (identifier)
# Notification subscription handled outside, notification management handled inside
def notification_create(*, action: str, sender_type: str, sender_id: int,
                           title: str, description: str, timestamp: int = None) -> NotificationObject:
    channel = get_object(NotificationChannel, action=action, sender_type=sender_type, sender_id=sender_id)
    notification_object = NotificationObject.objects.create(channel=channel,
                                                            title=title,
                                                            description=description,
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
                                   sender_type: str,
                                   sender_id: int) -> NotificationSubscription:
    channel = get_object(NotificationChannel, action=action, sender_type=sender_type, sender_id=sender_id)
    subscription = NotificationSubscription(user_id=user_id, channel=channel)
    subscription.full_clean()
    subscription.save()
    return subscription


def notification_channel_unsubscribe(*, user_id: int, action: str, sender_type: str, sender_id: int) -> None:
    channel = get_object(NotificationChannel, action=action, sender_type=sender_type, sender_id=sender_id)
    subscription = get_object(NotificationSubscription, user_id=user_id, channel=channel)
    subscription.delete()
    return
