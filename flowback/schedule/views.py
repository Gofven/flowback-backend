from rest_framework import serializers
from rest_framework.views import APIView
from flowback.common.pagination import LimitOffsetPagination


class ScheduleEventListAPI(APIView):
    class Pagination(LimitOffsetPagination):
        max_limit = 500

    class InputSerializer(serializers.Serializer):
        start_date = serializers.DateTimeField(required=False)
        start_date__lt = serializers.DateTimeField(required=False)
        start_date__gt = serializers.DateTimeField(required=False)

        end_date = serializers.DateTimeField(required=False)
        end_date__lt = serializers.DateTimeField(required=False)
        end_date__gt = serializers.DateTimeField(required=False)

        origin_name = serializers.CharField(required=False)
        origin_id = serializers.IntegerField(required=False)

    class OutputSerializer(serializers.Serializer):
        schedule_id = serializers.IntegerField()
        title = serializers.CharField()
        description = serializers.CharField(required=False)
        start_date = serializers.DateTimeField()
        end_date = serializers.DateTimeField(required=False)
        origin_name = serializers.CharField()
        origin_id = serializers.IntegerField()
        schedule_origin_name = serializers.CharField(source='schedule__origin_name')
        schedule_origin_id = serializers.CharField(source='schedule__origin_id')


class ScheduleEventCreateAPI(APIView):
    class InputSerializer(serializers.Serializer):
        title = serializers.CharField()
        description = serializers.CharField(required=False)

        start_date = serializers.DateTimeField()
        end_date = serializers.DateTimeField()

        origin_name = serializers.CharField()
        origin_id = serializers.IntegerField()


class ScheduleEventUpdateAPI(APIView):
    class InputSerializer(serializers.Serializer):
        title = serializers.CharField(required=False)
        description = serializers.CharField(required=False)
        start_date = serializers.DateTimeField(required=False)
        end_date = serializers.DateTimeField(required=False)


# ScheduleEventDeleteAPI don't need any templates
