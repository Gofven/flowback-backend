import django_filters
from django.db import models
from django.db.models import OuterRef, Q, Exists, Subquery, Count, F
from django_filters import FilterSet
from rest_framework.exceptions import ValidationError

from flowback.comment.models import Comment
from flowback.common.filters import NumberInFilter
from flowback.common.services import get_object
from flowback.group.models import Group, GroupUser, GroupThread
from flowback.poll.models import Poll, PollPredictionStatement
from flowback.schedule.selectors import schedule_event_list
from flowback.kanban.selectors import kanban_entry_list
from flowback.user.models import User, UserChatInvite
from backend.settings import env


class UserFilter(FilterSet):
    class Meta:
        model = User
        fields = {'id': ['exact'],
                  'username': ['exact', 'icontains']
                  }


def get_user(fetched_by: User, user_id: int = None):
    def user_to_dict(u, fields):
        return {field: getattr(user, field, None) for field in fields}

    if user_id:
        user = User.objects.get(id=user_id)

    else:
        user = fetched_by

    share_groups = User.objects.filter(group__groupuser__user__in=[fetched_by, user]).exists()

    if fetched_by == user:
        return user

    elif (user.public_status == User.PublicStatus.PUBLIC
          or (share_groups and user.public_status == User.PublicStatus.GROUP_ONLY)):
        return user_to_dict(user, ('id', 'username',
                                   'profile_image', 'banner_image',
                                   'public_status', 'chat_status',
                                   'bio', 'website', 'contact_email', 'contact_phone',
                                   'public_status'))

    else:
        return user_to_dict(user, ('id', 'username', 'profile_image',
                                   'banner_image', 'public_status', 'chat_status'))


def user_schedule_event_list(*, fetched_by: User, filters=None):
    filters = filters or {}
    return schedule_event_list(schedule_id=fetched_by.schedule.id, filters=filters)


def user_kanban_entry_list(*, fetched_by: User, filters=None):
    filters = filters or {}
    return kanban_entry_list(kanban_id=fetched_by.kanban.id, filters=filters, subscriptions=True)


def user_list(*, fetched_by: User, filters=None):
    # Block access to this api for members, unless group admin or higher.
    if env('FLOWBACK_GROUP_ADMIN_USER_LIST_ACCESS_ONLY') \
            and not Group.objects.filter(created_by=fetched_by).exists() \
            and not GroupUser.objects.filter(user=fetched_by, is_admin=True) \
            and not (fetched_by.is_staff and fetched_by.is_superuser):
        raise ValidationError('User must be group admin or higher')

    filters = filters or {}
    qs = User.objects.all()
    return UserFilter(filters, qs).qs


class UserHomeFeedFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(lookup_expr='exact')
    created_by_id = django_filters.NumberFilter(lookup_expr='exact')
    title = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    related_model = django_filters.CharFilter(lookup_expr='exact')
    group_joined = django_filters.BooleanFilter(lookup_expr='exact')
    group_ids = NumberInFilter(field_name='created_by__group_id')


# TODO add relevant Count (proposal, prediction, comments) to the home feed if possible
def user_home_feed(*, fetched_by: User, filters=None):
    filters = filters or {}
    joined_groups = Group.objects.filter(id=OuterRef('created_by__group_id'), groupuser__user__in=[fetched_by])
    related_fields = ['id',
                      'created_by',
                      'created_at',
                      'updated_at',
                      'group_id',
                      'title',
                      'description',
                      'related_model',
                      'group_joined']

    # Thread
    # threads = GroupThread.objects.filter(
    #     Q(created_by__group_id=group_id)
    #     & Q(Q(work_group__isnull=True)  # All threads without workgroup
    #         | Q(work_group__isnull=False) & Q(  # All threads with workgroup
    #             Q(work_group__workgroupuser__group_user=group_user))  # Check if groupuser is member in workgroup
    #         | Q(Q(created_by__group__groupuser=group_user) & Q(
    #             created_by__group__groupuser__is_admin=True)))  # Check if groupuser is admin in group
    # ).values('id')
    #
    # threads = GroupThread.objects.filter(id__in=[t['id'] for t in threads])  # TODO make this one query

    q = (Q(created_by__group__groupuser__user__in=[fetched_by]) & Q(created_by__group__groupuser__active=True)
         | Q(created_by__group__public=True) & ~Q(created_by__group__groupuser__user__in=[fetched_by])
         | Q(created_by__group__public=False) & Q(created_by__group__groupuser__user__in=[fetched_by])
         & Q(created_by__group__groupuser__active=False))

    thread_qs = GroupThread.objects.filter(q & Q(work_group__isnull=True)  # All threads without workgroup

                                           | Q(work_group__isnull=False)  # User in workgroup
                                           & Q(work_group__workgroupuser__group_user__user=fetched_by)

                                           | Q(work_group__isnull=False)  # User is admin in group
                                           & Q(created_by__group__groupuser__user=fetched_by)
                                           & Q(created_by__group__groupuser__is_admin=True))

    thread_qs = thread_qs.annotate(related_model=models.Value('group_thread', models.CharField()),
                                   group_id=F('created_by__group_id'),
                                   group_joined=Exists(joined_groups))
    thread_qs = thread_qs.values(*related_fields)
    thread_qs = UserHomeFeedFilter(filters, thread_qs).qs

    # Poll
    poll_qs = Poll.objects.filter(q)
    poll_qs = poll_qs.annotate(related_model=models.Value('poll', models.CharField()),
                               group_id=F('created_by__group_id'),
                               group_joined=Exists(joined_groups))
    poll_qs = poll_qs.values(*related_fields)
    poll_qs = UserHomeFeedFilter(filters, poll_qs).qs

    qs = thread_qs.union(poll_qs).order_by('-created_at')

    return qs


class UserChatInviteFilter(django_filters.FilterSet):
    user_id = django_filters.NumberFilter(field_name="user_id", lookup_expr="exact")
    message_channel_id = django_filters.NumberFilter(field_name="message_channel_id", lookup_expr="exact")
    rejected = django_filters.BooleanFilter(field_name="rejected", lookup_expr="exact")
    rejected__isnull = django_filters.BooleanFilter(field_name="rejected", lookup_expr="isnull")

    class Meta:
        model = UserChatInvite
        fields = ['user_id', 'message_channel_id', 'rejected', 'rejected__isnull']


def user_chat_invite_list(*, fetched_by: User, filters=None):
    filters = filters or {}

    qs = UserChatInvite.objects.filter(user=fetched_by).all()

    return UserChatInviteFilter(filters, qs).qs
