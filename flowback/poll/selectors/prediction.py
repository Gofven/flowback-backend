from typing import Union

import django_filters

from flowback.common.services import get_object
from flowback.group.selectors import group_user_permissions
from flowback.poll.models import PollPredictionStatement, Poll
from flowback.user.models import User


class BasePollPredictionStatementFilter(django_filters.FilterSet):
    proposals = django_filters.NumberFilter(field_name='proposal', lookup_expr='in')
    description = django_filters.CharFilter(lookup_expr='icontains')
    created_by_id = django_filters.NumberFilter(field_name='created_by_id', lookup_expr='exact')


    class Meta:
        model = PollPredictionStatement
        fields = dict(id=['exact'])


def poll_prediction_statement_list(*, fetched_by: User, poll: int, filters=None):
    filters = filters or {}

    poll = get_object(Poll, id=poll)
    group_user_permissions(group=poll.group.id, user=fetched_by)

    qs = PollPredictionStatement.objects.filter(poll_id=poll).all()
    return BasePollPredictionStatementFilter(filters, qs).qs
