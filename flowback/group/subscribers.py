from flowback.notification.services import notification_channel_subscribe, \
    notification_channel_unsubscribe
from flowback.group.services import group_user_permissions


def group_poll_feed_subscribe(group: int, fetched_by: int):
    user = group_user_permissions(group=group, user=fetched_by)
    return notification_channel_subscribe(user_id=fetched_by,
                                          action='create',
                                          sender_type='group',
                                          sender_id=user.group.id)



