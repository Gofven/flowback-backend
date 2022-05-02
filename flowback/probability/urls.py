from django.urls import path, include

from flowback.probability.views import ProbabilityPostListApi, ProbabilityVoteCreateApi, ProbabilityVoteDeleteApi, \
    ProbabilityVoteGetApi, ProbabilityUserGetApi

probability_patterns = [
    path('', ProbabilityPostListApi.as_view(), name='probability-list'),
    path('user', ProbabilityUserGetApi.as_view(), name='probability-user'),
    path('vote/<int:post>', ProbabilityVoteGetApi.as_view(), name='probability-vote-get'),
    path('vote/create', ProbabilityVoteCreateApi.as_view(), name='probability-vote-create'),
    path('vote/delete', ProbabilityVoteDeleteApi.as_view(), name='probability-vote-delete'),
]

urlpatterns = [
    path('prediction/', include((probability_patterns, 'prediction')))
]
