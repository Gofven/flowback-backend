import django_filters
from django.db.models import Q

from flowback.common.filters import NumberInFilter
from flowback.group.models import WorkGroupUser
from flowback.kanban.models import KanbanEntry


class BaseKanbanEntryFilter(django_filters.FilterSet):
    origin_type = django_filters.CharFilter(field_name='kanban__origin_type')
    origin_id = django_filters.NumberFilter(field_name='kanban_origin_id')
    created_by = django_filters.NumberFilter()
    work_group_id = NumberInFilter(field_name='work_group_id')
    order_by = django_filters.OrderingFilter(fields=(('priority', 'priority_asc'),
                                                     ('-priority', 'priority_desc')))
    assignee = django_filters.NumberFilter()

    class Meta:
        model = KanbanEntry
        fields = dict(title=['icontains'],
                      description=['icontains'],
                      end_date=['gt', 'lt'],
                      tag=['exact'],)


# TODO due for rework
def kanban_entry_list(*, group_user=None, kanban_id: int, subscriptions: bool, filters=None):
    filters = filters or {}

    if subscriptions:
        work_group_ids = WorkGroupUser.objects.filter(group_user=group_user).values_list('work_group_id')
        qs = KanbanEntry.objects.filter(Q(kanban_id=kanban_id) |
                                        Q(assignee__kanban__kanban_subscription_kanban=kanban_id)
                                        ).exclude(Q(work_group__isnull=False) & ~Q(work_group_id__in=work_group_ids)
                                                  ).distinct('id').all()

    else:
        qs = KanbanEntry.objects.filter(Q(kanban_id=kanban_id)).all()
    return BaseKanbanEntryFilter(filters, qs).qs
