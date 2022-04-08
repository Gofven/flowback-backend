from django.urls import path, include

from flowback.probability.views import ProbabilityPostListApi, ProbabilityVoteCreateApi, ProbabilityVoteDeleteApi

notification_patterns = [
    path('', ProbabilityPostListApi.as_view(), name='probability-list'),
    path('vote_create/', ProbabilityVoteCreateApi.as_view(), name='probability-vote-create'),
    path('vote_delete/', ProbabilityVoteDeleteApi.as_view(), name='probability-vote-delete')
]

urlpatterns = [
    path('probability/', include((notification_patterns, 'probability')))
]
