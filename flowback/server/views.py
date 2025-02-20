from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.views import APIView
from flowback.server.services import get_public_config


# Create your views here.
class ServerConfigListAPI(APIView):
    permission_classes = [AllowAny]

    class OutputSerializer(serializers.Serializer):
        DEBUG = serializers.BooleanField(help_text="Backend debug mode")
        FLOWBACK_KANBAN_LANES = serializers.ListField(
            child=serializers.CharField(),
            help_text="List of kanban lanes, when using the kanban list APIs, the kanban lanes represent the position "
                      "of the kanban 'lane' field, starting from 1")
        FLOWBACK_ALLOW_GROUP_CREATION = serializers.BooleanField(help_text='Allow users to create groups')
        FLOWBACK_ALLOW_DYNAMIC_POLL = serializers.BooleanField(help_text="Allow users to create dynamic polls")
        FLOWBACK_GROUP_ADMIN_USER_LIST_ACCESS_ONLY = serializers.BooleanField(
            help_text="Whether any group admins or superuser is able to list users or not or allow everyone to do that")
        FLOWBACK_DEFAULT_GROUP_JOIN = serializers.ListField(child=serializers.IntegerField(),
                                                            help_text="Default groups id's that users join")
        FLOWBACK_DISABLE_DEFAULT_USER_REGISTRATION = serializers.BooleanField(
            help_text="If users can register or not")

    def get(self, request):
        serializer = self.OutputSerializer(get_public_config())
        return Response(status=status, data=serializer.data)
