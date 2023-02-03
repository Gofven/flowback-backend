from django.db import models
from django.db.models import Q, OuterRef, Subquery, When, Case, F
import django_filters

from .models import GroupMessage, DirectMessage, GroupMessageUserData, DirectMessageUserData
from flowback.user.models import User
from flowback.group.models import GroupUser, Group
from flowback.group.services import group_user_permissions


class BaseGroupMessageFilter(django_filters.FilterSet):
    username__icontains = django_filters.CharFilter(field_name='group_user__user__username', lookup_expr='icontains')
    user = django_filters.NumberFilter(field_name='group_user__user', lookup_expr='exact')
    order_by = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at_asc'),
            ('-created_at', 'created_at_desc')
        )
    )

    class Meta:
        model = GroupMessage
        fields = dict(id=['exact'],
                      message=['icontains'],
                      created_at=['gt', 'lt'])


class BaseGroupMessagePreviewFilter(django_filters.FilterSet):
    group = django_filters.NumberFilter(field_name='group_user__group', lookup_expr='exact')
    group_name__icontains = django_filters.CharFilter(field_name='group_user__group__name', lookup_expr='icontains')

    class Meta:
        model = GroupMessage
        fields = dict(id=['exact'],
                      message=['icontains'],
                      created_at=['gt', 'lt'])


class BaseDirectMessageFilter(django_filters.FilterSet):
    order_by = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at_asc'),
            ('-created_at', 'created_at_desc')
        )
    )

    class Meta:
        model = DirectMessage
        fields = dict(id=['exact'],
                      target=['exact'],
                      message=['icontains'],
                      created_at=['gt', 'lt'])


class BaseDirectMessagePreviewFilter(django_filters.FilterSet):
    username__icontains = django_filters.CharFilter(field_name='target__username', lookup_expr='icontains')

    class Meta:
        model = DirectMessage
        fields = dict(id=['exact'],
                      created_at=['gt', 'lt'],
                      target=['exact'])


def group_message_list(*, user: User, group: int, filters=None):
    group_user_permissions(user=user, group=group)
    filters = filters or {}

    qs = GroupMessage.objects.filter(group_user__group=group).all()

    return BaseGroupMessageFilter(filters, qs).qs


def group_message_preview(*, user: User, filters=None):
    filters = filters or {}
    subquery = GroupMessageUserData.objects.filter(group_user__group=OuterRef('group_user__group'),
                                                   group_user__user=user).values('timestamp')
    qs = GroupMessage.objects.filter(group_user__group__groupuser__user__in=[user]
                                     ).order_by('group_user__group_id', '-created_at')\
        .annotate(timestamp=Subquery(subquery[:1])).distinct('group_user__group_id').all()
    return BaseGroupMessagePreviewFilter(filters, qs).qs


def direct_message_list(*, user: User, target: int, filters=None):
    filters = filters or {}
    qs = DirectMessage.objects.filter(Q(user=user, target_id=target) | Q(user_id=target, target=user)).all()

    return BaseDirectMessageFilter(filters, qs).qs


def direct_message_preview(*, user: User, filters=None):
    filters = filters or {}
    subquery = DirectMessageUserData.objects.filter(user=user,
                                                    target=Case(When(user=OuterRef('user'), then=OuterRef('target')),
                                                                default=OuterRef('user'))).values('timestamp')

    qs = DirectMessage.objects.filter(Q(user=user) | Q(target=user)
                                      ).annotate(relevant_user=Case(When(user=user, then=F('target')),
                                                                    When(target=user, then=F('user')))
                                                 ).order_by('relevant_user', '-created_at'
                                                            ).distinct('relevant_user').all()

    # TODO Find a better way to order this
    qs = DirectMessage.objects.filter(id__in=[q.id for q in qs]).annotate(timestamp=Subquery(subquery,
                                                                          output_field=models.DateTimeField()),
                                                                          ).order_by('-created_at').all()

    return BaseDirectMessagePreviewFilter(filters, qs).qs
