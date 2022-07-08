from django.db.models import Q
from django_filters import FilterSet, OrderingFilter

from .models import GroupMessage, DirectMessage
from flowback.users.models import GroupMembers
from flowback.users.services import group_user_permitted


class BaseGroupMessageFilter(FilterSet):
    o = OrderingFilter(
        fields=(
            ('created_at', 'created_at_asc'),
            ('-created_at', 'created_at_desc')
        )
    )

    class Meta:
        model = GroupMessage
        fields = 'user', 'message', 'created_at'


def group_message_list(*, user: int, group: int, filters=None):
    group_user_permitted(user=user,
                         group=group,
                         permission='member')

    filters = filters or {}

    qs = GroupMessage.objects.filter(group=group).all()

    return BaseGroupMessageFilter(filters, qs).qs


def group_message_preview(*, user: int):
    # TODO Does include guests
    groups = GroupMembers.objects.filter(user_id=user).values_list('group_id', flat=True)

    return GroupMessage.objects.filter(group__in=groups).order_by('group_id', '-created_at').distinct('group_id')


class BaseDirectMessageFilter(FilterSet):
    o = OrderingFilter(
        fields=(
            ('created_at', 'created_at_asc'),
            ('-created_at', 'created_at_desc')
        )
    )

    class Meta:
        model = DirectMessage
        fields = 'user', 'message', 'created_at'


def direct_message_list(*, user: int, target: int, filters=None):
    filters = filters or {}

    qs = DirectMessage.objects.filter(Q(user=user, target=target) | Q(user=target, target=user)).all()

    return BaseDirectMessageFilter(filters, qs).qs


def direct_message_preview(*, user: int):
    return DirectMessage.objects.filter(Q(user=user) | Q(target=user))\
           .order_by('user', 'target', 'created_at').distinct('user', 'target')
