from rest_framework import serializers, status, permissions
from rest_framework.views import APIView, Response

from flowback.common.mixins import ApiErrorsMixin
from flowback.common.pagination import LimitOffsetPagination, get_paginated_response
from flowback.probability.models import ProbabilityPost, ProbabilityVote, ProbabilityUser
from flowback.probability.selectors import probability_post_list, probability_get_vote, probability_get_user
from flowback.probability.services import probability_vote_create, probability_vote_delete, probability_post_check, \
    probability_count_votes


class ProbabilityPostListApi(ApiErrorsMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    class Pagination(LimitOffsetPagination):
        default_limit = 1

    class FilterSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        title = serializers.CharField(required=False)

    class OutputSerializer(serializers.ModelSerializer):
        id = serializers.SerializerMethodField()

        class Meta:
            model = ProbabilityPost
            fields = 'id', 'title', 'description', 'active', 'finished', 'result', 'created_at'

        def get_id(self, obj):
            probability_post_check(post=obj.id)
            return obj.id

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


class ProbabilityUserGetApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    class OutputSerializer(serializers.ModelSerializer):
        weight = serializers.IntegerField(source='trust')

        class Meta:
            model = ProbabilityUser
            fields = 'weight',

    def get(self, request, user_id=None):
        user = probability_get_user(user=user_id or request.user.id)
        serializer = self.OutputSerializer(user)
        return Response(data=serializer.data)


class ProbabilityVoteGetApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    class OutputSerializer(serializers.ModelSerializer):
        post = serializers.IntegerField(source='post.id')
        average = serializers.SerializerMethodField()

        class Meta:
            model = ProbabilityVote
            fields = 'post', 'score', 'average'

        def get_average(self, obj):
            return probability_count_votes(post=obj.post.id)

    def get(self, request, post: int):
        vote = probability_get_vote(user=request.user.id, post=post)

        serializer = self.OutputSerializer(vote)
        return Response(data=serializer.data)


class ProbabilityVoteCreateApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    class InputSerializer(serializers.Serializer):
        post = serializers.IntegerField()
        score = serializers.IntegerField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        probability_vote_create(user=request.user, **serializer.validated_data)

        return Response(status=status.HTTP_201_CREATED)


class ProbabilityVoteDeleteApi(APIView):
    permission_classes = [permissions.IsAuthenticated]

    class InputSerializer(serializers.Serializer):
        post = serializers.IntegerField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        probability_vote_delete(user=request.user, **serializer.validated_data)

        return Response(status=status.HTTP_200_OK)
