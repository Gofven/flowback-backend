from django.utils import timezone

from flowback.group.selectors import group_user_permissions
from flowback.kanban.models import KanbanEntry
from flowback.kanban.services import KanbanManager

group_kanban = KanbanManager(origin_type='group')


def group_kanban_entry_create(*,
                              group_id: int,
                              fetched_by_id: int,
                              assignee_id: int = None,
                              title: str,
                              description: str = None,
                              priority: int,
                              tag: int,
                              attachments: list = None,
                              end_date: timezone.datetime = None
                              ) -> KanbanEntry:
    group_user_permissions(group=group_id, user=fetched_by_id, permissions=['admin', 'create_kanban_task'])
    return group_kanban.kanban_entry_create(origin_id=group_id,
                                            created_by_id=fetched_by_id,
                                            assignee_id=assignee_id,
                                            title=title,
                                            description=description,
                                            attachments=attachments,
                                            priority=priority,
                                            end_date=end_date,
                                            tag=tag)


def group_kanban_entry_update(*,
                              fetched_by_id: int,
                              group_id: int,
                              entry_id: int,
                              data) -> KanbanEntry:
    group_user_permissions(group=group_id, user=fetched_by_id, permissions=['admin', 'update_kanban_task'])
    return group_kanban.kanban_entry_update(origin_id=group_id,
                                            entry_id=entry_id,
                                            data=data)


def group_kanban_entry_delete(*,
                              fetched_by_id: int,
                              group_id: int,
                              entry_id: int):
    group_user_permissions(group=group_id, user=fetched_by_id, permissions=['admin', 'delete_kanban_task'])
    return group_kanban.kanban_entry_delete(origin_id=group_id, entry_id=entry_id)
