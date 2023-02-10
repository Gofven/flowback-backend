# Schedule Event List (with multiple schedule id support)
import django_filters
from django.db.models import Q

from flowback.schedule.models import ScheduleEvent


class ScheduleEventBaseFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = ScheduleEvent
        fields = dict(start_date=['lt', 'gt', 'exact'],
                      end_date=['lt', 'gt', 'exact'],
                      origin_name=['exact'],
                      origin_id=['exact'])


def schedule_event_list(*, schedule_id: int, filters=None):
    filters = filters or {}
    qs = ScheduleEvent.objects.filter(Q(schedule_id=schedule_id) |
                                      Q(schedule__schedulesubscription__schedule_id=schedule_id))
    return ScheduleEventBaseFilter(filters, qs).qs
