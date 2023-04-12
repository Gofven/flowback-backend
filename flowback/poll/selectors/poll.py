from typing import Union

import django_filters
from django.db.models import Q, Exists, OuterRef
from django.utils import timezone
from flowback.group.models import Group
from flowback.poll.models import Poll
from flowback.user.models import User
from flowback.group.selectors import group_user_permissions


class BasePollFilter(django_filters.FilterSet):
    start_date = django_filters.DateFromToRangeFilter()
    end_date = django_filters.DateFromToRangeFilter()
    tag_name = django_filters.CharFilter(lookup_expr=['exact', 'icontains'], field_name='tag__name')

    class Meta:
        model = Poll
        fields = dict(id=['exact'],
                      created_by=['exact'],
                      title=['exact', 'icontains'],
                      poll_type=['exact'],
                      public=['exact'],
                      tag=['exact'],
                      finished=['exact'])


def poll_list(*, fetched_by: User, group_id: Union[int, None], filters=None):
    filters = filters or {}

    if group_id:
        group_user_permissions(group=group_id, user=fetched_by)
        qs = Poll.objects.filter(created_by__group_id=group_id).order_by('-id').all()

    else:
        joined_groups = Group.objects.filter(id=OuterRef('created_by__group_id'), groupuser__user__in=[fetched_by])
        qs = Poll.objects.filter((Q(created_by__group__groupuser__user__in=[fetched_by]) | Q(public=True))
                                 & Q(start_date__lte=timezone.now())).annotate(group_joined=Exists(joined_groups))\
            .order_by('-id').distinct('id').all()

    return BasePollFilter(filters, qs).qs
