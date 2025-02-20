from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from flowback.common.pagination import LimitOffsetPagination, get_paginated_response

from flowback.group.models import GroupTags
from flowback.group.selectors import group_tags_list, group_tags_interval_mean_absolute_correctness
from flowback.group.services.tag import (group_tag_create,
                                         group_tag_update,
                                         group_tag_delete)


@extend_schema(tags=['group/tag'])
class GroupTagsListApi(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 1

    class FilterSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        tag_name = serializers.CharField(required=False)
        tag_name__icontains = serializers.CharField(required=False)
        active = serializers.BooleanField(required=False, default=None, allow_null=True)

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = GroupTags
            fields = ('id', 'name', 'active')

    def get(self, request, group: int):
        filter_serializer = self.FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        tags = group_tags_list(group=group,
                               fetched_by=request.user,
                               filters=filter_serializer.validated_data)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=tags,
            request=request,
            view=self
        )


# TODO make this a part of GroupTagsListAPI
@extend_schema(tags=['group/tag'])
class GroupTagIntervalMeanAbsoluteCorrectnessAPI(APIView):
    def get(self, request, tag_id: int):
        val = group_tags_interval_mean_absolute_correctness(tag_id=tag_id, fetched_by=request.user)
        return Response(status=status.HTTP_200_OK, data=val)


@extend_schema(tags=['group/tag'])
class GroupTagsCreateApi(APIView):
    class InputSerializer(serializers.ModelSerializer):
        class Meta:
            model = GroupTags
            fields = ('name',)

    def post(self, request, group: int):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group_tag_create(user=request.user.id, group=group, **serializer.validated_data)

        return Response(status=status.HTTP_200_OK)


@extend_schema(tags=['group/tag'])
class GroupTagsUpdateApi(APIView):
    class InputSerializer(serializers.Serializer):
        tag = serializers.IntegerField()
        active = serializers.BooleanField()

    def post(self, request, group: int):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tag = serializer.validated_data.pop('tag')

        group_tag_update(user=request.user.id, group=group, tag=tag, data=serializer.validated_data)

        return Response(status=status.HTTP_200_OK)


@extend_schema(tags=['group/tag'])
class GroupTagsDeleteApi(APIView):
    class InputSerializer(serializers.Serializer):
        tag = serializers.IntegerField()

    def post(self, request, group: int):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tag = serializer.validated_data.pop('tag')

        group_tag_delete(user=request.user.id, group=group, tag=tag)

        return Response(status=status.HTTP_200_OK)
