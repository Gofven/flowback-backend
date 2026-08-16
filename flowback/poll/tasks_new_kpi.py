from django.db.models import (
    Count,
    OuterRef,
    F,
    Subquery,
)
from flowback.group.models import (
    Group,
)
from flowback.poll.phases import (
    PollProposalKPI,
    PollProposalKPIBet,
)

from flowback.poll.services.prediction import longest_poll_prediction_kpi_group_users
import numpy as np


def newer_kpi_betting(group: Group):
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
    # Outcome värde 1 på vinnande KPI värden (baserat på pluralitetsröstning)
    # Outcome värde 0 på andra KPI värden
    # Ta random när lika
    # Historiken lägs till när evaluering har skett. (HURRRR SKA MAN HITTA LÄNGSTA DÅ)
    # Det är bara KPI på vinnande proposalen man tar med

    # Betta - Outcome
    # 1 predictor 1 poll
    # Exempel: 1,2 5%, 3 90%
    # Vinnande i tidigare historik 3
    #
    # Outcome - Betts
    # [0.05, 0.05, -0.1]
    # Betta - Outcome
    # [-0.05, -0.05, 0.1]

    # 2 polls och 2 predictors
    # Ordning av polls och evaluering borde inte spela roll
    # 0% 0% 100%
    # 33% 33% 34%
    # Evalueras 3
    # Efter en poll
    # [0,    0,     0   ]
    # [0.33, 0.33, -0.66]
    # Efter two poll
    # 0% 0% 100%
    # 33% 33% 34%
    # Evalueras 3
    # [0,    0,     0,    0,    0,     0   ]
    # [0.33, 0.33, -0.66, 0.33, 0.33, -0.66]
    # Nånting om np arrays idk
    # tag 3 kolumner (i detta fall) ska inte spela roll
    # tag rader ska inte spela roll

    longest_users = longest_poll_prediction_kpi_group_users(group, users_filter=None)

    bets = PollProposalKPIBet.objects.filter(
        created_by__in=longest_users,
        proposal_kpi__pollproposalkpivote__isnull=False,
    ).distinct()

    # for example: 90 --> 0.9
    bets = normalize_bets(bets)

    winning_kpis = get_winning_kpi_values(group)

    input_matrix = bet_outcome_matrix(bets, winning_kpis)

    return method(input_matrix)


def normalize_bets(bets):
    weights = np.array(list(bets.values_list("weight", flat=True)), dtype=float)
    return weights / weights.sum()


def method(input_matrix):
    # Might be always convex
    P_1 = np.cov(input_matrix)
    result = quadratic_programming_solver(P_1)[0]
    return result


def get_winning_kpi_values(group: Group):

    winner = (
        PollProposalKPI.objects
        .filter(
            proposal=OuterRef("proposal"),
            kpi_value__kpi=OuterRef("kpi_value__kpi"),
            proposal__poll__created_by__group=group
        )
        .annotate(votes=Count("pollproposalkpivote"))
        .filter(votes__gt=0)
        .order_by("-votes")
        .values("id")[:1]
    )

    winning_kpis = (
        PollProposalKPI.objects
        .annotate(winner=Subquery(winner))
        .filter(id=F("winner"))
    )

    return winning_kpis


def bet_outcome_matrix(bets, winner_index):
    bets = np.asarray(bets, dtype=float)
    outcome = np.zeros(bets.shape[-1])
    outcome[winner_index] = 1

    difference = bets - outcome
    return np.array([difference, -difference]) if bets.ndim == 1 else difference


def quadratic_programming_solver(covariance_matrix, test=False):
    import cvxpy as cp

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

    weight_solution = predictor_weights.value
    minimum_variance = optimization_problem.value
    nonnegativity_dual_values = nonnegativity_constraint.dual_value

    if test:
        print("\nThe optimal value is", minimum_variance)
        print("A solution x is")
        print(weight_solution)

    # weight_solution is a vector (np.array) that sums up to 1.
    return [weight_solution, minimum_variance, nonnegativity_dual_values]
