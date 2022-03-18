from django.shortcuts import get_object_or_404
from rest_framework.validators import ValidationError
from flowback.probability.models import ProbabilityPost, ProbabilityUser, ProbabilityVote


def probability_vote_create(*, user: int, post: int):
    user = ProbabilityUser.objects.get_or_create(user=user)
    post = get_object_or_404(ProbabilityPost, post=post)

    ProbabilityVote.objects.create(user=user, post=post.id)


def probability_vote_delete(*, user: int, post: int):
    vote = get_object_or_404(ProbabilityVote, user=user, post=post)

    vote.delete()
