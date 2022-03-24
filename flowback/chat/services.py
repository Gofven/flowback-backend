from channels.db import database_sync_to_async
from django.shortcuts import get_object_or_404

from flowback.users.models import User, Group
from flowback.chat.models import GroupMessage
from flowback.users.services import group_user_permitted


@database_sync_to_async
def group_channel_connect(*, self, user: int, group: int):
    user = get_object_or_404(User, user_id=user)
    group = get_object_or_404(Group, group_id=group)

    if not group_user_permitted(user=user.id,
                                group=group.id,
                                permission='member',
                                raise_exception=False):
        return self.close()

    return group


@database_sync_to_async
def group_channel_message(*, user: int, group: int, message: str):
    user = get_object_or_404(User, user_id=user)
    group = get_object_or_404(Group, group_id=group)

    GroupMessage.objects.create(user=user,
                                group=group,
                                message=message)
