from django.urls import path, include

from flowback.probability.views import ProbabilityPostListApi, ProbabilityVoteCreateApi, ProbabilityVoteDeleteApi, \
    ProbabilityVoteGetApi

probability_patterns = [
    path('', ProbabilityPostListApi.as_view(), name='probability-list'),
    path('vote/<int:vote>', ProbabilityVoteGetApi, name='probability-vote-get'),
    path('vote/create', ProbabilityVoteCreateApi.as_view(), name='probability-vote-create'),
    path('vote/delete', ProbabilityVoteDeleteApi.as_view(), name='probability-vote-delete')
]

urlpatterns = [
    path('probability/', include((probability_patterns, 'prediction')))
]
