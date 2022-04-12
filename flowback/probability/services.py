from django.db.models import Avg, F, Sum
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from flowback.probability.models import ProbabilityPost, ProbabilityUser, ProbabilityVote


def probability_vote_create(*, user: int, post: int, score: int):
    probability_post_check(post=post)

    user = ProbabilityUser.objects.get_or_create(user=user)
    post = get_object_or_404(ProbabilityPost, pk=post)

    if not (post.active or post.finished):
        return ValidationError('Post is inactive or finished.')

    ProbabilityVote.objects.create(user=user, post=post.id, score=score)


def probability_vote_delete(*, user: int, post: int):
    probability_post_check(post=post)

    vote = get_object_or_404(ProbabilityVote, user=user, post=post)

    if not (vote.post.active or vote.post.finished):
        return ValidationError('Post is inactive, or finished.')

    vote.delete()


def probability_count_votes(*, post: int):
    post = get_object_or_404(ProbabilityPost, pk=post)
    total_votes = ProbabilityVote.objects.filter(post=post).count()

    # Get the average votes, multiply by 20 at the end
    return ProbabilityVote.objects.filter(post=post).aggregate(
        total=((Sum('vote') * 20) * (Sum('user__trust') / 100)) / total_votes
    ).get('total')


def probability_post_finish(*, post: int):
    post = get_object_or_404(ProbabilityPost, pk=post)
    votes = ProbabilityVote.objects.filter(post=post).all()

    # Round values to steps of 20 then divide by 20 to have same values as ProbabilityVote models
    average = round(probability_count_votes(post=post.id) / 20)

    for vote in votes:
        vote.user.trust += (vote.score - average) * (1 if post.result else -1) * 10

        if vote.user.trust <= 0:
            vote.user.trust = 1

    ProbabilityUser.objects.bulk_update([x.user for x in votes], ['trust'])


def probability_post_check(*, post: int):
    post = get_object_or_404(ProbabilityPost, pk=post)

    probability_count_votes(post=post.id)

    if post.finished and post.active:
        probability_post_finish(post=post.id)
        post.active = False
        post.save()
