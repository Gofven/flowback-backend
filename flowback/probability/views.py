from rest_framework import serializers, status, permissions
from rest_framework.views import APIView, Response

from flowback.common.mixins import ApiErrorsMixin
from flowback.common.pagination import LimitOffsetPagination, get_paginated_response
from flowback.probability.models import ProbabilityPost, ProbabilityVote
from flowback.probability.selectors import probability_post_list
from flowback.probability.services import probability_vote_create, probability_vote_delete, probability_count_votes


class ProbabilityPostListApi(ApiErrorsMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    class Pagination(LimitOffsetPagination):
        default_limit = 1

    class FilterSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        title = serializers.CharField(required=False)

    class OutputSerializer(serializers.ModelSerializer):
        score = serializers.SerializerMethodField()

        class Meta:
            model = ProbabilityPost
            fields = 'title', 'description', 'active', 'finished', 'result', 'created_at'

        def get_score(self, obj):
            return probability_count_votes(post=obj.post)

    def get(self, request):
        filter_serializer = self.FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        probability_posts = probability_post_list(filters=filter_serializer.validated_data)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=probability_posts,
            request=request,
            view=self
        )


class ProbabilityVoteCreateApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    class InputSerializer(serializers.ModelSerializer):
        class Meta:
            model = ProbabilityVote
            fields = 'post', 'vote', 'score'

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        probability_vote_create(user=request.user, **serializer.validated_data)

        return Response(status=status.HTTP_201_CREATED)


class ProbabilityVoteDeleteApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    class InputSerializer(serializers.ModelSerializer):
        class Meta:
            model = ProbabilityVote
            fields = 'post'

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        probability_vote_delete(user=request.user, **serializer.validated_data)

        return Response(status=status.HTTP_200_OK)
