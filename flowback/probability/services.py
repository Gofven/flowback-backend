from django.db.models import Avg, F, Sum
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from flowback.probability.models import ProbabilityPost, ProbabilityUser, ProbabilityVote


def probability_vote_create(*, user: int, post: int, score: int):
    user = ProbabilityUser.objects.get_or_create(user=user)
    post = get_object_or_404(ProbabilityPost, post=post)

    if not (post.active or post.finished):
        return ValidationError('Post is inactive or finished.')

    ProbabilityVote.objects.create(user=user, post=post.id, score=score)


def probability_vote_delete(*, user: int, post: int):
    vote = get_object_or_404(ProbabilityVote, user=user, post=post)

    if not (vote.post.active or vote.post.finished):
        return ValidationError('Post is inactive or finished.')

    vote.delete()


def probability_count_votes(*, post: int):
    post = get_object_or_404(ProbabilityPost, post=post)

    # Get the average votes, multiply by 20 at the end
    return ProbabilityVote.objects.filter(post=post).aggregate(
        total=(F('vote') * F('user__trust')) / Sum(F('user__trust'))
    ).get('total') * 20


def probability_post_finish(*, post: int):
    post = get_object_or_404(ProbabilityPost, post=post)
    votes = ProbabilityUser.objects.filter(post=post).all()

    # Round values to steps of 20, eg 29.94 becomes 20,
    # then divide by 20 to have same values as ProbabilityVote models
    average = round(probability_count_votes(post=post.id) / 20)

    for vote in votes:
        score = (vote.score - average) * (1 if post.result else -1) * 10
