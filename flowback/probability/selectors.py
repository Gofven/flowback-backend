import django_filters
from django.shortcuts import get_object_or_404

from flowback.probability.models import ProbabilityPost, ProbabilityVote, ProbabilityUser


class BaseProbabilityPostFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = ProbabilityPost
        fields = 'title',


def probability_post_list(*, filters=None):
    filters = filters or {}
    qs = ProbabilityPost.objects.all().order_by('-created_at')

    return BaseProbabilityPostFilter(filters, qs).qs


def probability_get_vote(*, user: int, post: int):
    return ProbabilityVote.objects.get(user__user=user, post=post)


def probability_get_user(*, user: int):
    return ProbabilityUser.objects.get(user=user)
