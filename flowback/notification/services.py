from .models import NotificationChannel, Notification, NotificationSubscription
from ..user.models import User


def notification_update(*, user: User,
                        notification_object_ids: list[Notification | int],
                        read: bool) -> None:
    notifications = Notification.objects.filter(subscriber__user=user,
                                                notification_object_id__in=notification_object_ids)

    notifications.update(read=read)


def notification_subscribe(*,
                           user: User,
                           channel: NotificationChannel | int,
                           tags: list[str]) -> NotificationSubscription | None:

    # Delete subscription if no categories are present
    if not tags:
        NotificationSubscription.objects.get(user=user, channel=channel).delete()
        return None

    subscription, created = NotificationSubscription.objects.update_or_create(user=user,
                                                                              channel=channel,
                                                                              defaults=dict(tags=tags))

    return subscription


## notification_delete
## notification_mark_read
## notification_channel_subscribe
## notification_channel_unsubscribe
