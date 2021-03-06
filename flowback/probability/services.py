from django.db.models import Avg, F, Sum
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from flowback.probability.models import ProbabilityPost, ProbabilityUser, ProbabilityVote


def probability_vote_create(*, user: int, post: int, score: int):
    probability_post_check(post=post)

    user = ProbabilityUser.objects.get_or_create(user=user)[0]
    post = get_object_or_404(ProbabilityPost, pk=post)

    if not post.active or post.finished:
        raise ValidationError('Post is inactive or finished.')

    ProbabilityVote.objects.update_or_create(user=user, post=post, defaults=dict(score=score))


def probability_vote_delete(*, user: int, post: int):
    probability_post_check(post=post)

    vote = get_object_or_404(ProbabilityVote, user__user=user, post=post)

    if not (vote.post.active or vote.post.finished):
        raise ValidationError('Post is inactive, or finished.')

    vote.delete()


def probability_count_votes(*, post: int):
    post = get_object_or_404(ProbabilityPost, pk=post)

    # If the vote has been concluded, return the saved result
    if post.finished and not post.active:
        return post.score

    total_votes = ProbabilityVote.objects.filter(post=post).count()

    # Get the average votes, multiply by 20 at the end
    print(ProbabilityVote.objects.filter(post=post).aggregate(score=Sum('score'), trust=Sum('user__trust')))
    val = ProbabilityVote.objects.filter(post=post).aggregate(
        total=(Sum(F('score') * 20 * F('user__trust') / 100) / total_votes)
    )

    return val.get('total')


def probability_post_finish(*, post: int):
    post = get_object_or_404(ProbabilityPost, pk=post)
    votes = ProbabilityVote.objects.filter(post=post).prefetch_related('user').all()

    post.score = probability_count_votes(post=post.id)


    # Round values to steps of 20 then divide by 20 to have same values as ProbabilityVote models
    average = round(probability_count_votes(post=post.id) / 20)

    for vote in votes:
        vote.user.trust += (vote.score - average) * (1 if post.result else -1) * 10

        if vote.user.trust <= 0:
            vote.user.trust = 10
        elif vote.user.trust > 100:
            vote.user.trust = 100

    ProbabilityUser.objects.bulk_update([x.user for x in votes], ['trust'])

    post.active = False
    post.save()


def probability_post_check(*, post: int):
    post = get_object_or_404(ProbabilityPost, pk=post)

    probability_count_votes(post=post.id)

    if post.finished and post.active:
        probability_post_finish(post=post.id)
