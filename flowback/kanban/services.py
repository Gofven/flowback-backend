from flowback.common.services import get_object, model_update
from flowback.group.services import group_notification
from flowback.kanban.models import KanbanEntry
from flowback.group.selectors import group_user_permissions


def kanban_entry_create(*,
                        user_id: int,
                        group_id: int,
                        assignee_id: int,
                        title: str,
                        description: str,
                        tag: int) -> KanbanEntry:
    created_by = group_user_permissions(user=user_id, group=group_id)
    assignee = group_user_permissions(user=assignee_id, group=group_id)
    kanban = KanbanEntry(created_by_id=created_by.id, assignee_id=assignee.id,
                         title=title, description=description, tag=tag)

    kanban.full_clean()
    kanban.save()

    group_notification.create(sender_id=group_id, action=group_notification.Action.create, category='kanban',
                              message=f'User {created_by.user.username} created a kanban in {created_by.group.name}')

    return kanban


def kanban_entry_update(*, fetched_by: int, group_id: int, kanban_entry_id: int, data) -> KanbanEntry:
    group_user = group_user_permissions(group=group_id, user=fetched_by)
    kanban = get_object(KanbanEntry, id=kanban_entry_id, group_user__group_id=group_id)

    if data.get('assignee_id'):
        data['assignee'] = group_user_permissions(group=group_id, user=data['assignee_id'])

    non_side_effect_fields = ['title', 'description', 'assignee', 'tag']

    kanban, has_updated = model_update(instance=kanban,
                                       fields=non_side_effect_fields,
                                       data=data)

    group_notification.create(sender_id=group_id, action=group_notification.Action.update, category='kanban',
                              message=f'User {group_user.user.username} updated a kanban in {group_user.group.name}')

    return kanban


def kanban_entry_delete(*, fetched_by: int, group_id: int, kanban_entry_id: int) -> None:
    group_user = group_user_permissions(group=group_id, user=fetched_by)
    get_object(KanbanEntry, id=kanban_entry_id, created_by__group_id=group_id).delete()

    group_notification.create(sender_id=group_id, action=group_notification.Action.delete, category='kanban',
                              message=f'User {group_user.user.username} deleted a kanban in {group_user.group.name}')
