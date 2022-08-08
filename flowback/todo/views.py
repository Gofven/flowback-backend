from flowback.todo.models import Todo
from flowback.todo.services import todo_create, todo_delete
from flowback.todo.selectors import todo_get

from flowback.common.mixins import ApiErrorsMixin
from rest_framework.views import APIView, Response
from rest_framework import serializers, status


class TodoCreateApi(APIView, ApiErrorsMixin):
    class InputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Todo
            fields = 'category', 'content'

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        todo_create(user=request.user.id, **serializer.data)


class TodoGetApi(APIView, ApiErrorsMixin):
    def get(self, request):
        return Response(todo_get(user=request.user.id), status=status.HTTP_200_OK)


class TodoDeleteApi(APIView, ApiErrorsMixin):
    class InputSerializer(serializers.Serializer):
        id = serializers.IntegerField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        todo_delete(**serializer.validated_data)
