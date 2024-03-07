from celery import shared_task
from django.db.models import Count, Q

from flowback.common.services import get_object
from flowback.group.models import GroupTags
from flowback.poll.models import Poll, PollAreaStatement, PollPredictionBet

import numpy as np


@shared_task
def poll_area_vote_count(poll_id: int):
    poll = get_object(Poll, id=poll_id)
    statement = PollAreaStatement.objects.filter(poll=poll).annotate(
        result=Count('pollareastatementvote', filter=Q(pollareastatementvote__vote=True)) -
               Count('pollareastatementvote', filter=Q(pollareastatementvote__vote=False))).order_by('-result').first()

    if statement:
        tag = GroupTags.objects.filter(pollareastatementsegment__poll_area_statement_id=statement).first()
        poll.tag = tag
        poll.save()

        # Clean all area tag votes, we won't need it anymore
        PollAreaStatement.objects.filter(poll=poll).delete()

    return poll


@shared_task
def poll_prediction_bet_count(poll_id: int):
    # Get every predictor participating in poll

    # Get list of bets in the given poll, ordered
    #   - if any bet missing, dismiss count
    PollPredictionBet.objects.filter(prediction_statement__poll_id=poll_id)

    # Get list of previous outcomes in a given area (poll)

    # For one prediction, assuming no bias and stationary predictors




    # TODO solve how to handle missing prediction bets
    # The following two comments is a possible solution that inserts nan into the matrix
    # import numpy.ma as ma
    # cv = ma.cov(ma.masked_invalid(my_matrix), rowvar=False)
    # Otherwise, the standard solution is to skip the value for all predictors

    # In a given area
    outcomes = [0, 1, 1, 0, 1]

    # Current bets by each predictor in order
    current_bets = np.array([[0.5], [0.5]])

    # Constructing the predictor error matrix
    predictor_1_bets = [0, 0.4, 0.6, 0, 1]
    predictor_2_bets = [0, 0.4, 0.4, 0, 1]
    predictor_1_errors = np.array([outcomes[i] - predictor_1_bets[i] for i in range(len(outcomes))])
    predictor_2_errors = np.array([outcomes[i] - predictor_2_bets[i] for i in range(len(outcomes))])

    predictor_errors = [predictor_1_errors, predictor_2_errors]

    predictor_error_matrix = np.array([predictor_1_errors, predictor_2_errors])

    #If a predictor has not bet on a certain prediction then
    # their bet will be None for said prediction
    def drop_incomparable_values(arr_1, arr_2):
        for i in range(len(arr_1)):
            if arr_1[i] or arr_2[i] is None:
                arr_1.pop(i)
                arr_2.pop(i)
        return arr_1, arr_2

    def covariance(arr_1, arr_2):
        covariance_array = [(arr_1[i] - np.mean(arr_1))*(arr_2[i] - np.mean(arr_2)) for i in range(len(arr_1))]
        return (1/len(arr_1))*sum(covariance_array)

    covariance_matrix_1 = []
    for i in range(len(predictor_errors)):
        row = []
        for j in range(len(predictor_errors)):
            comparable_errors = drop_incomparable_values(predictor_errors[i], predictor_errors[j])
            row.append(covariance(comparable_errors[0], comparable_errors[1]))
        covariance_matrix_1.append(row)

    print(covariance_matrix_1)

    # Code below is checked and correct

    covariance_matrix = np.cov(predictor_error_matrix, ddof=0)

    inverse_covariance_matrix = np.linalg.inv(covariance_matrix)

    column_one_vector = np.array([[1]] * inverse_covariance_matrix.shape[0])
    row_one_vector = np.array([1] * inverse_covariance_matrix.shape[0])

    nominator = np.matmul(inverse_covariance_matrix, column_one_vector)

    denominator_vector = np.matmul(inverse_covariance_matrix, row_one_vector)
    denominator = np.matmul(row_one_vector, denominator_vector)

    bet_weights = nominator * (1 / denominator)
    transposed_bet_weights = np.transpose(bet_weights)

    combined_bet = np.matmul(transposed_bet_weights, current_bets)

    print(combined_bet)

