from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ..models import (PollPrediction,
                      PollPredictionStatement,
                      PollPredictionStatementSegment,
                      PollPredictionStatementVote,
                      Poll, PollProposal)
from ...common.services import get_object
from ...group.selectors import group_user_permissions


# Prediction Statement Create (with segments)
def poll_prediction_statement_create(poll: int,
                                     user: int,
                                     description: str,
                                     end_date: timezone.datetime,
                                     segments: dict):
    poll = get_object(Poll, id=poll)
    group_user = group_user_permissions(group=poll.group, user=user)
    prediction_statement = PollPredictionStatement(created_by=group_user,
                                                   poll=poll,
                                                   description=description,
                                                   end_date=end_date)

    valid_proposals = PollProposal.objects.filter(id__in=segments, poll__group=group_user.group)
    prediction_statement.full_clean()

    if len(valid_proposals) == len(segments):
        prediction_statement_segment = [PollPredictionStatementSegment(proposal=segment['proposal'],
                                                                       is_true=segment['is_true'],
                                                                       prediction_statement=prediction_statement)
                                        for segment in segments]

        prediction_statement.save()
        PollPredictionStatementSegment.objects.bulk_create(prediction_statement_segment)
        return prediction_statement.id

    else:
        raise ValidationError('Prediction statement segment(s) contains invalid proposal')


# Prediction Statement Update (with segments)

# Prediction Statement Delete

# Prediction Create

# Prediction Update

# Prediction Delete

# Prediction Statement Vote Create

# Prediction Statement Vote Update

# Prediction Statement Vote Delete
