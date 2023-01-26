from django.utils import timezone
from rest_framework.exceptions import ValidationError

from flowback.common.services import get_object
from flowback.group.selectors import group_user_permissions
from flowback.poll.models import PollProposal, Poll, PollProposalTypeSchedule


# TODO proposal can be created without schedule, dangerous
def poll_proposal_create(*, user_id: int, group_id: int, poll_id: int,
                         title: str = None, description: str = None, **data) -> PollProposal:
    group_user = group_user_permissions(user=user_id, group=group_id)
    poll = get_object(Poll, id=poll_id)

    if group_user.group.id != poll.created_by.group.id:
        raise ValidationError('Permission denied')

    if poll.proposal_end_date <= timezone.now():
        raise ValidationError("Can't create a proposal after proposal end date")

    proposal = PollProposal(created_by=group_user, poll=poll, title=title, description=description)

    proposal.full_clean()
    proposal.save()

    extra = []
    if poll.poll_type == Poll.PollType.SCHEDULE:
        if not data.get('start_date') and not data.get('end_date'):
            raise Exception('Missing start_date and/or end_date, for proposal schedule creation')

        extra.append(PollProposalTypeSchedule(proposal=proposal, start_date=data['start_date'],
                                              end_date=data['end_date']))

    for extension in extra:
        extension.full_clean()
        extension.save()

    return proposal


def poll_proposal_delete(*, user_id: int, group_id: int, poll_id: int, proposal_id: int) -> None:
    group_user = group_user_permissions(user=user_id, group=group_id)
    proposal = get_object(PollProposal, id=proposal_id, poll_id=poll_id)

    if proposal.poll.proposal_end_date <= timezone.now():
        raise ValidationError("Can't delete a proposal after proposal end date")

    if not proposal.created_by == group_user:
        raise ValidationError('Permission denied')

    if group_user.group.id != proposal.poll.created_by.group.id:
        raise ValidationError('Permission denied')

    if proposal.poll.finished:
        raise ValidationError('Only site administrators and above can delete proposals after the poll is finished.')

    proposal.delete()
