from django.shortcuts import get_object_or_404
from django.utils.datetime_safe import datetime
from rest_framework.exceptions import ValidationError

from flowback.chat.models import MessageChannel, Message, MessageChannelParticipant, MessageFileCollection
from flowback.common.services import get_object, model_update
from flowback.files.services import upload_collection
from flowback.user.models import User


def create_message(*,
                   user_id: int,
                   channel_id: int,
                   message: str,
                   upload_to: str,
                   attachments: list = None,
                   parent_id: int = None):
    user = get_object(User, user=user_id)
    channel = get_object(MessageChannel, channel=channel_id)
    parent = get_object(Message, id=parent_id, raise_exception=False)

    if parent and parent.channel.id != channel_id:
        raise ValidationError('Parent does not exist')

    attachments = upload_collection(user_id=user_id,
                                    file=attachments,
                                    upload_to=upload_to)

    message = Message(user=user,
                      channel=channel,
                      message=message,
                      attachments=attachments,
                      parent=parent)

    message.full_clean()
    message.save()

    return message


def update_message(*, user_id: int, message_id: int, **data):

    user = get_object(User, user=user_id)
    message = get_object(Message, id=message_id)

    if not user == message.user:
        raise ValidationError('User is not author of message')

    fields = ['message']

    model_update(instance=message,
                 fields=fields,
                 data=data)


def delete_message(*, user_id: int, message_id: int):
    user = get_object(User, user=user_id)
    message = get_object(Message, id=message_id)

    if not user == message.user:
        raise ValidationError('User is not author of message')

    message.message = ""
    message.active = False
    message.save()


def upload_message_files(*, user_id: int, channel_id: int, files: list) -> MessageFileCollection:
    user = get_object(User, user=user_id)
    channel = get_object(MessageChannel, id=channel_id)
    upload_to = f"{MessageFileCollection.attachments_upload_to}/{channel.origin_name}"

    file_collection = upload_collection(user_id=user_id, file=files,
                                        upload_to=upload_to)

    message_collection = MessageFileCollection(user=user, channel=channel, file_collection=file_collection)
    message_collection.full_clean()
    message_collection.save()

    return message_collection


def update_message_channel_userdata(*, user_id: int, channel_id: int, timestamp: datetime):
    user = get_object(User, user=user_id)
    channel = get_object(MessageChannel, id=channel_id)

    if not channel.message_set.filter(user=user).exists():
        raise ValidationError('User never sent message in channel')

    user_data = MessageChannelParticipant.objects.get_or_create(user=user, channel=channel, timestamp=timestamp)

    if not user_data[1]:
        user_data[0].timestamp = timestamp
        user_data[0].save()

    return user_data[0]


def leave_message_channel(*, user_id: int, channel_id: int):
    user = get_object(User, user=user_id)
    channel = get_object(MessageChannel, id=channel_id)
    participant = get_object(MessageChannelParticipant, user=user, channel=channel)

    participant.delete()
