from typing import cast

from django.db.models import (
    Count,
    OuterRef,
    F,
    QuerySet,
    Subquery,
    Window
)
from django.db.models.functions import Random, RowNumber
from numpy.typing import NDArray

from flowback.group.models import (
    Group,
)
from flowback.poll.phases import (
    PollProposalKPI,
    PollProposalKPIBet,
)

from flowback.poll.services.prediction import longest_poll_prediction_kpi_group_users
import numpy as np
import cvxpy as cp



def newer_kpi_betting(group: Group) -> NDArray[np.float64] | None:
    """
    This code was primarily written by Loke Hagberg 2026-06-12
    This work was made possible by my wonderful best friend: Emil Svenberg

    Track record handling 1 (might be a second track record handling or more later)

    When calculating the combined probability, pick the largest set of participating predictors with longest (within some max number)
    and fully overlapping track records are there multiple, pick one uniformly randomly.

    Example: If 1 predictor has participated 3 times on winning polls, and 5 predictors has participated 2 times, then this calculation
    takes just 1 predictor as input (with history of 3).

    It is valuable to know what the value of the determinant is, one can use numpy.linalg.det(matrix) for that purpose
    Save all determinants as how near one is to a singular matrix the more sensitive the method chosen is to input data

    Methods for calculating the combined probability

    The DCP rules in cvxpy require that the problem objective have one of two forms: Minimize(convex) or Maximize(concave)

    Long term TODO: Formal verification in an functional language (Haskell? F#? Scala?).
    Also a compiled program/binary with this can avoid numpy and cvxpy bloat in the rest of flowback without a microservice.
    """
    # Outcome value 1 for winning KPI values (based on plurality voting)
    # Outcome value 0 for other KPI values
    # Choose randomly when tied
    # History is added after evaluation. (HOW DO YOU FIND THE LONGEST HISTORY THEN?)
    # Only include KPIs from the winning proposal

    # Bet - Outcome
    # 1 predictor 1 poll
    # Example: values 1 and 2 get 5%; value 3 gets 90%
    # Winner in previous history: 3
    #
    # Outcome - Betts
    # [0.05, 0.05, -0.1]
    # Bet - Outcome
    # [-0.05, -0.05, 0.1]

    # 2 polls and 2 predictors
    # Poll and evaluation order should not matter
    # 0% 0% 100%
    # 33% 33% 34%
    # Evaluated as 3
    # After one poll
    # [0,    0,     0   ]
    # [0.33, 0.33, -0.66]
    # After two polls
    # 0% 0% 100%
    # 33% 33% 34%
    # Evaluated as 3
    # [0,    0,     0,    0,    0,     0   ]
    # [0.33, 0.33, -0.66, 0.33, 0.33, -0.66]
    # Something about NumPy arrays, unclear
    # Number of columns (3 in this case) should not matter
    # Number of rows should not matter

    longest_users = longest_poll_prediction_kpi_group_users(group, users_filter=None)

    bets_qs = PollProposalKPIBet.objects.filter(
        created_by__in=longest_users,
    ).distinct()

    winning_kpis_qs = get_winning_kpi_values(group)

    input_matrix = bet_outcome_matrix(bets_qs, winning_kpis_qs)

    return method(input_matrix)


def get_winning_kpi_values(group: Group) -> QuerySet[PollProposalKPI]:
    winning_kpis = (
        PollProposalKPI.objects
        .filter(proposal__poll__created_by__group=group)
        .annotate(votes=Count("pollproposalkpivote"))
        .filter(votes__gt=0)
        .annotate(
            winner_rank=Window(
                expression=RowNumber(),
                partition_by=[
                    F("proposal_id"),
                    F("kpi_value__kpi_id"),
                ],
                order_by=[
                    F("votes").desc(),
                    Random(),
                ],
            )
        )
        .filter(winner_rank=1)
    )

    return winning_kpis


def bet_outcome_matrix(
    bets: QuerySet[PollProposalKPIBet],
    winning_kpis: QuerySet[PollProposalKPI],
) -> NDArray[np.float64]:
    bets = list(bets)
    winning_kpis = list(winning_kpis.order_by("proposal_id", "kpi_value__kpi_id"))
    columns = [
        proposal_kpi
        for winner in winning_kpis
        for proposal_kpi in PollProposalKPI.objects.filter(
            proposal=winner.proposal,
            kpi_value__kpi=winner.kpi_value.kpi,
        ).order_by("id")
    ]
    bet_values = {
        (bet.created_by_id, bet.proposal_kpi_id): bet.weight / 100
        for bet in bets
    }
    predictor_ids = sorted({bet.created_by_id for bet in bets})
    matrix = np.array(
        [
            [
                bet_values.get((predictor_id, column.id), 0)
                - (column in winning_kpis)
                for column in columns
            ]
            for predictor_id in predictor_ids
        ],
        dtype=float,
    )

    return np.vstack((matrix, -matrix)) if len(matrix) == 1 else matrix


def method(input_matrix: NDArray[np.float64]) -> NDArray[np.float64] | None:
    # Might be always convex
    covariance_matrix = np.cov(input_matrix)
    result = quadratic_programming_solver(covariance_matrix)[0]
    return cast(NDArray[np.float64] | None, result)


def quadratic_programming_solver(
    covariance_matrix: NDArray[np.float64], test: bool = False
) -> list[NDArray[np.float64] | float | None]:
    if np.any((covariance_matrix < 0) | (covariance_matrix > 1)):
        raise ValueError(
            "covariance_matrix entries must be between 0 and 1 (inclusive)"
        )

    predictor_count = covariance_matrix.shape[0]
    # No negative probabilities
    nonnegativity_coefficients = -np.identity(predictor_count)
    nonnegativity_bounds = np.zeros(predictor_count)
    # All probabilities add to one
    normalization_coefficients = np.ones(predictor_count)

    # Define and solve the CVXPY problem.
    predictor_weights = cp.Variable(predictor_count)
    nonnegativity_constraint = (
        nonnegativity_coefficients @ predictor_weights <= nonnegativity_bounds
    )

    normalization_constraint = normalization_coefficients.T @ predictor_weights == 1
    optimization_problem = cp.Problem(
        # @ is matmul
        # .T is transpose
        # With method 1, the covariance matricies that can be inputed are always convex
        cp.Minimize(cp.quad_form(predictor_weights, covariance_matrix)),
        [nonnegativity_constraint, normalization_constraint],
    )

    # Convex case
    try:
        optimization_problem.solve()

    # Concave case
    except Exception:
        print("Concave minimization")
        # TODO: for Emil: extend the algorithm to include the concave minimization case
        # Might not actually be needed tbh

    weight_solution = predictor_weights.value
    minimum_variance = optimization_problem.value
    nonnegativity_dual_values = nonnegativity_constraint.dual_value

    if test:
        print("\nThe optimal value is", minimum_variance)
        print("A solution x is")
        print(weight_solution)

    # weight_solution is a vector (np.array) that sums up to 1.
    return [weight_solution, minimum_variance, nonnegativity_dual_values]
