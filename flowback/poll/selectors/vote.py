import django_filters
from rest_framework.exceptions import ValidationError

from flowback.common.services import get_object
from flowback.poll.models import Poll, PollDelegateVoting, PollVotingTypeCardinal, PollVotingTypeForAgainst
from flowback.user.models import User
from flowback.group.selectors.permission import group_user_permissions


class BaseDelegatePollVoteFilter(django_filters.FilterSet):
    class Meta:
        model = PollDelegateVoting
        fields = dict(poll_id=['exact'])


class BasePollVoteCardinalFilter(django_filters.FilterSet):
    delegate_pool_id = django_filters.NumberFilter(field_name='author_delegate__created_by')
    delegate_user_id = django_filters.NumberFilter(
        field_name='author_delegate__created_by__groupuserdelegate__group_user__user_id')

    class Meta:
        model = PollVotingTypeCardinal
        fields = dict(proposal=['exact'])


class BasePollDelegateVotingFilter(django_filters.FilterSet):
    delegate_pool_id = django_filters.NumberFilter(field_name='created_by_id')

    class Meta:
        model = PollDelegateVoting
        fields = dict(poll_id=['exact'])


def delegate_poll_vote_list(*, fetched_by: User, group_id: int, **filters):
    filters = filters or {}
    group_user_permissions(user=fetched_by, group=group_id)
    qs = PollDelegateVoting.objects.filter(poll__created_by__group_id=group_id).distinct()
    return BaseDelegatePollVoteFilter(filters, qs).qs


class BasePollVoteForAgainstFilter(django_filters.FilterSet):
    created_by_user_id = django_filters.NumberFilter(field_name='author__created_by__user_id')

    class Meta:
        model = PollVotingTypeForAgainst
        fields = dict(proposal_id=['exact'])


def poll_vote_list(*, fetched_by: User, poll_id: int, delegates: bool = False, filters=None):
    poll = get_object(Poll, id=poll_id)

    filters = filters or {}

    # Schedule (For Against)
    qs = PollVotingTypeForAgainst.objects.filter(proposal__poll=poll).order_by('-vote').all()
    if poll.created_by.group.hide_poll_users:
        filters['created_by_user_id'] = fetched_by.id

    return BasePollVoteForAgainstFilter(filters, qs).qs



def poll_delegates_list(*, fetched_by: User, poll_id: int, filters=None):
    filters = filters or {}

    poll = get_object(Poll, id=poll_id)
    group_user_permissions(user=fetched_by, group=poll.created_by.group.id)

    qs = PollDelegateVoting.objects.filter(poll=poll).all()
    return BasePollDelegateVotingFilter(filters, qs).qs
