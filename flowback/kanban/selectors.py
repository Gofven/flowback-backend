import django_filters
from django.db.models import Q

from flowback.kanban.models import KanbanEntry


class BaseKanbanEntryFilter(django_filters.FilterSet):
    origin_type = django_filters.CharFilter(field_name='kanban__origin_type')
    origin_id = django_filters.NumberFilter(field_name='kanban_origin_id')
    created_by = django_filters.NumberFilter()
    assignee = django_filters.NumberFilter()

    class Meta:
        model = KanbanEntry
        fields = dict(title=['icontains'],
                      description=['icontains'],
                      tag=['exact'])


def kanban_list(*, kanban_id: int, filters=None):
    filters = filters or {}

    qs = KanbanEntry.objects.filter(Q(kanban_id=kanban_id) |
                                    Q(kanban__kanbansubscription__kanban=kanban_id)).all()
    return BaseKanbanEntryFilter(filters, qs).qs
