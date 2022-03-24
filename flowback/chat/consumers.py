import json
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import GroupMessage
from flowback.users.models import User, Group
from flowback.users.services import group_user_permitted


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.group_id = self.scope['url_route']['kwargs']['group_id']

        if self.scope['user'].is_anonymous:
            await self.close()

        self.group = await self.group_channel_connect()

        # Join room group
        await self.channel_layer.group_add(
            self.group_id,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.group_id,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.group_id,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from room group
    async def chat_message(self, message: str):
        class OutputSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = 'username', 'image'

        data = OutputSerializer(self.user).data

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user': data
        }))

    @database_sync_to_async
    def group_channel_connect(self):
        group = get_object_or_404(Group, pk=self.group_id)
        group_user_permitted(user=self.user.id,
                             group=self.group_id,
                             permission='member')

        return group

    @database_sync_to_async
    def group_channel_message(self, message):
        GroupMessage.objects.create(user=self.user,
                                    group=self.group,
                                    message=message)
