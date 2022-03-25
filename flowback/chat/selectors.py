import django_filters
from .models import GroupMessage
from flowback.users.services import group_user_permitted


class BaseGroupMessageFilter(django_filters.FilterSet):
    class Meta:
        model = GroupMessage
        fields = 'user', 'message', 'created_at'


def group_message_list(*, user: int, group: int, filters=None):
    group_user_permitted(user=user,
                         group=group,
                         permission='member')

    filters = filters or {}

    qs = GroupMessage.objects.all()

    return BaseGroupMessageFilter(filters, qs).qs


def group_message_preview(*, user: int):
    return