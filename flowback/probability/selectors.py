import django_filters

from flowback.probability.models import ProbabilityPost


class BaseProbabilityPostFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = ProbabilityPost
        fields = 'id'


def probability_post_list(*, filters=None):
    filters = filters or {}
    qs = ProbabilityPost.objects.all()

    return BaseProbabilityPostFilter(filters, qs)