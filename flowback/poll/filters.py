import django_filters

from flowback.common.filters import ExistsFilter, NumberInFilter
from flowback.poll.phases import PollProposal


class BasePollProposalFilter(django_filters.FilterSet):
    group = django_filters.NumberFilter(field_name='created_by__group_id', lookup_expr='exact')
    created_by_user_id_list = NumberInFilter(field_name='created_by__user_id')
    order_by = django_filters.OrderingFilter(fields=(('created_at', 'created_at_asc'),
                                                     ('-created_at', 'created_at_desc'),
                                                     ('score', 'score_asc'),
                                                     ('-score', 'score_desc')))
    has_attachments = ExistsFilter(field_name='attachments')

    class Meta:
        model = PollProposal
        fields = dict(id=['exact'],
                      created_by=['exact'],
                      title=['exact', 'icontains'])


class BasePollProposalScheduleFilter(django_filters.FilterSet):
    order_by = django_filters.OrderingFilter(
        fields=(
            ('start_date', 'start_date_asc'),
            ('-start_date', 'start_date_desc'),
            ('end_date', 'end_date_asc'),
            ('-end_date', 'end_date_desc'),
        )
    )

    group = django_filters.NumberFilter(field_name='created_by.group_id', lookup_expr='exact')

    start_date__lt = django_filters.DateTimeFilter(field_name='pollproposaltypeschedule.event_start_date',
                                                   lookup_expr='lt')
    start_date__gte = django_filters.DateTimeFilter(field_name='pollproposaltypeschedule.event_start_date',
                                                    lookup_expr='gte')
    end_date__lt = django_filters.DateTimeFilter(field_name='pollproposaltypeschedule.event_end_date',
                                                 lookup_expr='lt')
    end_date__gte = django_filters.DateTimeFilter(field_name='pollproposaltypeschedule.event_end_date',
                                                  lookup_expr='gte')

    poll_title = django_filters.CharFilter(field_name='poll.title', lookup_expr='exact')
    poll_title__icontains = django_filters.CharFilter(field_name='poll.title', lookup_expr='icontains')

    class Meta:
        model = PollProposal
        fields = dict(id=['exact'],
                      created_by=['exact'],
                      title=['exact', 'icontains'])
