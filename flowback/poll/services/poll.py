from rest_framework.exceptions import ValidationError
from flowback.common.services import get_object, model_update
from flowback.group.services import group_notification, group_schedule
from flowback.notification.services import NotificationManager
from flowback.poll.models import Poll, PollProposal
from flowback.group.selectors import group_user_permissions
from django.utils import timezone
from datetime import datetime

from flowback.poll.services.vote import poll_proposal_vote_count

poll_notification = NotificationManager(sender_type='poll', possible_categories=['timeline',
                                                                                 'poll',
                                                                                 'comment_self',
                                                                                 'comment_all'])


def poll_notification_subscribe(*, user_id: int, poll_id: int, categories: list[str]):
    poll = get_object(Poll, id=poll_id)
    group_user_permissions(user=user_id, group=poll.created_by.group.id)

    poll_notification.channel_subscribe(user_id=user_id, sender_id=poll.id, category=categories)


def poll_create(*, user_id: int,
                group_id: int,
                title: str,
                description: str,
                start_date: datetime,
                proposal_end_date: datetime,
                vote_start_date: datetime,
                delegate_vote_end_date: datetime,
                end_date: datetime,
                poll_type: int,
                public: bool,
                tag: int,
                pinned: bool,
                dynamic: bool
                ) -> Poll:
    group_user = group_user_permissions(user=user_id, group=group_id, permissions=['create_poll', 'admin'])

    if not group_user.is_admin and pinned:
        raise ValidationError('Permission denied')

    poll = Poll(created_by=group_user, title=title, description=description,
                start_date=start_date, proposal_end_date=proposal_end_date, vote_start_date=vote_start_date,
                delegate_vote_end_date=delegate_vote_end_date, vote_end_date=end_date, end_date=end_date,
                poll_type=poll_type, public=public, tag_id=tag, pinned=pinned, dynamic=dynamic)
    poll.full_clean()
    poll.save()

    # Group notification
    group_notification.create(sender_id=group_id, action=poll_notification.Action.update, category='poll',
                              message=f'User {group_user.user.username} created poll {poll.title}',
                              timestamp=start_date, related_id=poll.id)

    # Poll notification
    poll_notification.create(sender_id=poll.id, action=poll_notification.Action.update, category='timeline',
                             message=f'Poll {poll.title} has stopped accepting proposals',
                             timestamp=proposal_end_date)

    poll_notification.create(sender_id=poll.id, action=poll_notification.Action.update, category='timeline',
                             message=f'Poll {poll.title} has started accepting votes',
                             timestamp=vote_start_date)

    poll_notification.create(sender_id=poll.id, action=poll_notification.Action.update, category='timeline',
                             message=f'Poll {poll.title} has stopped accepting delegate votes',
                             timestamp=delegate_vote_end_date)

    poll_notification.create(sender_id=poll.id, action=poll_notification.Action.update, category='timeline',
                             message=f'Poll {poll.title} has finished',
                             timestamp=end_date)

    if poll_type == Poll.PollType.SCHEDULE:
        group_notification.create(sender_id=group_id, action=group_notification.Action.update, category='schedule',
                                  message=f'Poll {poll.title} has finished, group schedule has been updated')

    return poll


def poll_update(*, user_id: int, poll_id: int, data) -> Poll:
    poll = get_object(Poll, id=poll_id)
    group_user = group_user_permissions(user=user_id, group=poll.created_by.group.id)

    if not poll.created_by == group_user or not group_user.is_admin:
        raise ValidationError('Permission denied')

    if not group_user.is_admin and data.get('pinned', False):
        raise ValidationError('Permission denied')

    non_side_effect_fields = ['title', 'description', 'pinned']

    poll, has_updated = model_update(instance=poll,
                                     fields=non_side_effect_fields,
                                     data=data)

    return poll


# TODO remove related notifications
def poll_delete(*, user_id: int, poll_id: int) -> None:
    poll = get_object(Poll, id=poll_id)
    group_id = poll.created_by.group.id
    group_user = group_user_permissions(user=user_id, group=group_id)

    force_deletion_access = group_user_permissions(group_user=group_user, permissions=['admin', 'force_delete_poll'],
                                                   raise_exception=False)

    if poll.created_by == group_user and not force_deletion_access:
        if poll.start_date < timezone.now():
            raise ValidationError("Unable to delete ongoing polls")

        if poll.finished:
            raise ValidationError("Unable to delete finished polls")

    else:
        group_user_permissions(group_user=group_user, permissions=['admin', 'force_delete_poll'])

    # Remove future notifications
    if timezone.now() <= poll.start_date:
        group_notification.delete(sender_id=group_id, category='poll', related_id=poll.id)

    if timezone.now() <= poll.proposal_end_date:
        poll_notification.delete(sender_id=poll_id, category='timeline', timestamp__gt=poll.proposal_end_date)
    elif timezone.now() <= poll.vote_start_date:
        poll_notification.delete(sender_id=poll_id, category='timeline', timestamp__gt=poll.vote_start_date)
    elif timezone.now() <= poll.delegate_vote_end_date:
        poll_notification.delete(sender_id=poll_id, category='timeline', timestamp__gt=poll.delegate_vote_end_date)
    elif timezone.now() <= poll.end_date:
        poll_notification.delete(sender_id=poll_id, category='timeline', timestamp__gt=poll.end_date)

    poll.delete()


def poll_finish(*, poll_id: int) -> None:
    poll = get_object(Poll, id=poll_id)

    if poll.finished:
        raise ValidationError("Poll is already finished")

    poll_proposal_vote_count(poll_id=poll_id)
    poll.finished = True
    poll.result = True
    poll.save()


def poll_refresh(*, poll_id: int) -> None:
    poll = get_object(Poll, id=poll_id)

    if not poll.dynamic:
        raise ValidationError("Attempted to refresh a poll that doesn't allow live update")

    if poll.finished:
        raise ValidationError("Attempted to refresh a poll that's already finished")

    poll_proposal_vote_count(poll_id=poll_id)


# TODO setup celery
def poll_refresh_cheap(*, poll_id: int) -> None:
    poll = get_object(Poll, id=poll_id)
    if poll.end_date <= timezone.now() and not poll.result:
        poll.finished = True
        poll.save()

    if (poll.finished and not poll.result) or (poll.dynamic and not poll.finished):
        poll_proposal_vote_count(poll_id=poll_id)
        poll.refresh_from_db()
        poll.result = True

        # Add the event if the poll finished
        if poll.poll_type == Poll.PollType.SCHEDULE:
            event = PollProposal.objects.filter(poll=poll).order_by('score')
            if event.exists():
                event = event.first().pollproposaltypeschedule
                group_schedule.create_event(schedule_id=poll.created_by.group.schedule_id,
                                            title=poll.title,
                                            start_date=event.start_date,
                                            end_date=event.end_date,
                                            origin_name='poll',
                                            origin_id=poll.id,
                                            description=poll.description)

        poll.save()
