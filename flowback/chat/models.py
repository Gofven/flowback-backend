from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import models
from django.db.models.signals import post_delete, post_save

from backend.settings import TESTING
from flowback.common.models import BaseModel
from flowback.files.models import FileCollection


class MessageChannel(BaseModel):
    origin_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, null=True, blank=True)
    users = models.ManyToManyField('user.User', through='chat.MessageChannelParticipant')


# Allows for "channels" inside a group
class MessageChannelTopic(BaseModel):
    channel = models.ForeignKey(MessageChannel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    hidden = models.BooleanField(default=False)


class MessageChannelParticipant(BaseModel):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    channel = models.ForeignKey(MessageChannel, on_delete=models.CASCADE)
    closed_at = models.DateTimeField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    @classmethod
    def post_save(cls, instance, created, **kwargs):
        if created:  # Only send for new messages
            if not TESTING:
                channel_layer = get_channel_layer()

                # Send the message to the group
                async_to_sync(channel_layer.group_send)(
                    f"{instance.channel.id}",
                    dict(type="info",
                         method="message_notify",
                         message=f"User {instance.user.username} joined the channel")
                )



    @classmethod
    def post_delete(cls, instance, created, **kwargs):
        if created:  # Only send for new messages
            if not TESTING:
                channel_layer = get_channel_layer()

                # Send the message to the group
                async_to_sync(channel_layer.group_send)(
                    f"{instance.channel.id}",
                    dict(type="info",
                         method="message_notify",
                         message=f"User {instance.user.username} joined the channel")
                )



    class Meta:
        unique_together = ('user', 'channel')

post_save.connect(MessageChannelParticipant.post_save, sender=MessageChannelParticipant)
post_delete.connect(MessageChannelParticipant.post_delete, sender=MessageChannelParticipant)


# For image attachments
class MessageFileCollection(BaseModel):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    channel = models.ForeignKey(MessageChannel, on_delete=models.CASCADE)
    file_collection = models.ForeignKey(FileCollection, on_delete=models.CASCADE)

    @property
    def attachments_upload_to(self):
        return 'message'


class Message(BaseModel):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    channel = models.ForeignKey(MessageChannel, on_delete=models.CASCADE)
    topic = models.ForeignKey(MessageChannelTopic, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField(max_length=2000)
    attachments = models.ForeignKey(MessageFileCollection,
                                    on_delete=models.SET_NULL,
                                    null=True,
                                    blank=True)  # TODO instead of MessageFileCollection, use FileCollection directly
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='message_parent')
    active = models.BooleanField(default=True)
