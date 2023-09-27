from rest_framework.exceptions import ValidationError

from flowback.common.services import get_object, model_update
from flowback.group.selectors import group_user_permissions
from flowback.poll.models import PollAreaStatement, PollAreaStatementSegment, PollAreaStatementVote, Poll


def poll_area_statement_create(user_id: int, poll_id: int, tags: list[int]):
    poll = get_object(Poll, id=poll_id)
    group_user = group_user_permissions(user=user_id, group=poll.created_by.group)

    poll.check_phase('area_vote')

    # Create Statement
    poll_area_statement = PollAreaStatement(created_by=group_user, poll=poll)

    poll_area_statement.full_clean()
    poll_area_statement.save()

    # Create Segments
    poll_area_statement_segments = [PollAreaStatementSegment(poll_area_statement=poll_area_statement,
                                                             tag_id=i) for i in tags]

    PollAreaStatementSegment.objects.bulk_create(poll_area_statement_segments)


def poll_area_statement_delete(user_id: int, poll_area_statement_id: int):
    poll_area_statement = get_object(PollAreaStatement,
                                     id=poll_area_statement_id,
                                     created_by__user_id=user_id)
    poll = get_object(Poll, id=poll_area_statement.poll.id)

    poll.check_phase('area_vote')

    poll_area_statement.delete()


def poll_area_statement_vote_update(user_id: int, poll_area_statement_id: int, vote: bool):
    poll_area_statement = get_object(PollAreaStatement,
                                     id=poll_area_statement_id,
                                     created_by__user_id=user_id)
    poll = get_object(Poll, id=poll_area_statement.poll.id)
    group_user = group_user_permissions(user=user_id, group=poll.created_by.group)

    poll.check_phase('area_vote')

    # Create or Update
    PollAreaStatementVote.objects.update_or_create(created_by=group_user,
                                                   poll_area_statement=poll_area_statement,
                                                   defaults=dict(vote=vote))
