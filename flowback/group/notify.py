from flowback.group.models import WorkGroupUser, GroupThread
from flowback.kanban.models import KanbanEntry
from flowback.notification.models import NotificationChannel
from flowback.user.models import User


def notify_group_kanban(message: str,
                        action: NotificationChannel.Action,
                        kanban_entry: KanbanEntry,
                        user: User | int = None):
    user_id = user if isinstance(user, int) or user is None else user.id
    group = kanban_entry.kanban.group_set.first()

    if kanban_entry.work_group:
        users = [user_id] if user else kanban_entry.work_group.group_users.values_list('user_id', flat=True)

        group.notify_kanban(message=message,
                            action=NotificationChannel.Action.CREATED,
                            work_group_id=kanban_entry.work_group_id,
                            work_group_name=kanban_entry.work_group.name,
                            kanban_entry_id=kanban_entry.id,
                            subscription_filters=dict(user_id__in=users))

    else:
        group.notify_kanban(message=message,
                            action=action,
                            kanban_entry_id=kanban_entry.id,
                            subscription_filters=dict(user_id=user_id) if user else None)


def notify_group_thread(message: str,
                        action: NotificationChannel.Action,
                        thread: GroupThread):
    subscription_filters = None

    if thread.work_group:
        subscription_filters = dict(user_id__in=thread.work_group.group_users.values_list('user_id', flat=True))

    GroupThread.created_by.group.notify_thread(message=message,
                                               action=action,
                                               thread_id=thread.id,
                                               thread_title=thread.title,
                                               work_group_id=thread.work_group_id if thread.work_group else None,
                                               work_group_name=thread.work_group.name if thread.work_group else None,
                                               subscription_filters=subscription_filters)
