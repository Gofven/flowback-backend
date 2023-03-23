from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ..models import (PollPrediction,
                      PollPredictionStatement,
                      PollPredictionStatementSegment,
                      PollPredictionStatementVote,
                      Poll, PollProposal)
from ...common.services import get_object, model_update
from ...group.selectors import group_user_permissions


# Prediction Statement Create (with segments)
def poll_prediction_statement_create(poll: int,
                                     user: int,
                                     description: str,
                                     end_date: timezone.datetime,
                                     segments: dict) -> int:
    poll = get_object(Poll, id=poll)
    group_user = group_user_permissions(group=poll.group, user=user)
    prediction_statement = PollPredictionStatement(created_by=group_user,
                                                   poll=poll,
                                                   description=description,
                                                   end_date=end_date)

    valid_proposals = PollProposal.objects.filter(id__in=segments, poll__group=group_user.group)
    prediction_statement.full_clean()

    if prediction_statement.poll.vote_start_date > timezone.now():
        raise ValidationError("Unable to create prediction statement before poll proposal start date")

    if len(segments < 1):
        raise ValidationError('Prediction statement must contain atleast one statement')

    elif len(valid_proposals) == len(segments):
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
def poll_prediction_statement_update(user: int, prediction_statement: int) -> None:
    prediction_statement = get_object(PollPredictionStatement, id=prediction_statement)
    group_user = group_user_permissions(group=prediction_statement.poll.group, user=user)

    if not prediction_statement.created_by == group_user:
        raise ValidationError('Prediction statement not created by user')


# Prediction Statement Delete
def poll_prediction_statement_delete(user: int, prediction_statement: int) -> None:
    prediction_statement = get_object(PollPredictionStatement, id=prediction_statement)
    group_user = group_user_permissions(group=prediction_statement.poll.group, user=user)

    if not prediction_statement.created_by == group_user:
        raise ValidationError('Prediction statement not created by user')

    prediction_statement.delete()

# Prediction Create
def poll_prediction_create(user: int, prediction_statement: int, score: int) -> int:
    prediction_statement = get_object(PollPredictionStatement, id=prediction_statement)
    group_user = group_user_permissions(group=prediction_statement.poll.group, user=user)

    if prediction_statement.end_date < timezone.now():
        raise ValidationError("Unable to create predictions after prediction statement end date")

    prediction = PollPrediction(created_by=group_user,
                                prediction_statement=prediction_statement,
                                score=score)
    prediction.full_clean()
    prediction.save()

    return prediction.id

# Prediction Update
def poll_prediction_update(user: int, prediction: int, data) -> int:
    prediction = get_object(PollPrediction, id=prediction)
    group_user = group_user_permissions(group=prediction.poll.group, user=user)

    if prediction.prediction_statement.end_date < timezone.now():
        raise ValidationError("Unable to update predictions after prediction statement end date")

    if not prediction.created_by == group_user:
        raise ValidationError('Prediction not created by user')

    non_side_effect_fields = ['score']
    prediction, has_updated = model_update(instance=prediction,
                                           fields=non_side_effect_fields,
                                           data=data)
    prediction.full_clean()
    prediction.save()

    return prediction.id

# Prediction Delete
def poll_prediction_delete(user: int, prediction: int):
    prediction = get_object(PollPrediction, id=prediction)
    group_user = group_user_permissions(group=prediction.poll.group, user=user)

    if prediction.prediction_statement.end_date < timezone.now():
        raise ValidationError("Unable to delete predictions after prediction statement end date")

    if not prediction.created_by == group_user:
        raise ValidationError('Prediction not created by user')

    prediction.delete()

# Prediction Statement Vote Create
def poll_prediction_statement_vote_create(user: int, prediction_statement: int, vote: bool):
    prediction_statement = get_object(PollPredictionStatement, id=prediction_statement)
    group_user = group_user_permissions(group=prediction_statement.poll.group, user=user)

    if prediction_statement.end_date < timezone.now():
        raise ValidationError("Unable to vote ahead of prediction statement end date")

    prediction_vote = PollPredictionStatementVote(created_by=group_user,
                                                  prediction_statement=prediction_statement,
                                                  vote=vote)
    prediction_vote.full_clean()
    prediction_vote.save()

# Prediction Statement Vote Update
def poll_prediction_statement_vote_update(user: int,
                                          prediction_statement_vote: int,
                                          data) -> PollPredictionStatementVote:
    prediction_statement_vote = get_object(PollPredictionStatementVote, id=prediction_statement_vote)
    group_user = group_user_permissions(group=prediction_statement_vote.prediction_statement.poll.group, user=user)

    if prediction_statement_vote.created_by != group_user:
        raise ValidationError('Prediction statement vote not created by user')

    non_side_effect_fields = ['vote']
    prediction_statement_vote, has_updated = model_update(instance=prediction_statement_vote,
                                                          fields=non_side_effect_fields,
                                                          data=data)

    return prediction_statement_vote

# Prediction Statement Vote Delete
def poll_prediction_statement_vote_delete(user: int, prediction_statement_vote: int):
    prediction_statement_vote = get_object(PollPredictionStatementVote, id=prediction_statement_vote)
    group_user = group_user_permissions(group=prediction_statement_vote.prediction_statement.poll.group, user=user)

    if prediction_statement_vote.created_by != group_user:
        raise ValidationError('Prediction statement vote not created by user')

    prediction_statement_vote.delete()
