import logging
import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.db.models.signals import post_save, post_delete, pre_save
from django.forms import model_to_dict
from rest_framework.exceptions import ValidationError

from backend.settings import FLOWBACK_DEFAULT_GROUP_JOIN
from flowback.chat.models import MessageChannel, MessageChannelParticipant
from flowback.comment.models import CommentSection, comment_section_create, comment_section_create_model_default
from flowback.common.models import BaseModel
from flowback.files.models import FileCollection
from flowback.kanban.models import Kanban, KanbanSubscription
from flowback.schedule.models import Schedule
from flowback.user.models import User
from django.db import models


# Create your models here.
class GroupFolder(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f'{self.id} - {self.name}'


class Group(BaseModel):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    # Direct join determines if join requests requires moderation or not.
    direct_join = models.BooleanField(default=False)

    # Public determines if the group is open to public or not
    public = models.BooleanField(default=True)

    # Determines the default permission for every user get when they join
    # TODO return basic permissions by default if field is NULL
    default_permission = models.OneToOneField('GroupPermissions',
                                              null=True,
                                              blank=True,
                                              on_delete=models.SET_NULL)

    name = models.TextField(unique=True)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='group/image', null=True, blank=True)
    cover_image = models.ImageField(upload_to='group/cover_image', null=True, blank=True)
    hide_poll_users = models.BooleanField(default=False)  # Hides users in polls, TODO remove bool from views
    poll_phase_minimum_space = models.IntegerField(default=0)  # The minimum space between poll phases (in seconds)
    default_quorum = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    schedule = models.ForeignKey(Schedule, null=True, blank=True, on_delete=models.PROTECT)
    kanban = models.ForeignKey(Kanban, null=True, blank=True, on_delete=models.PROTECT)
    chat = models.ForeignKey(MessageChannel, on_delete=models.PROTECT)
    group_folder = models.ForeignKey(GroupFolder, null=True, blank=True, on_delete=models.SET_NULL)
    blockchain_id = models.PositiveIntegerField(null=True, blank=True, help_text='User-Defined Blockchain ID')

    jitsi_room = models.UUIDField(unique=True, default=uuid.uuid4)

    class Meta:
        constraints = [models.CheckConstraint(check=~Q(Q(public=False) & Q(direct_join=True)),
                                              name='group_not_public_and_direct_join_check')]

    @classmethod
    def pre_save(cls, instance, raw, using, update_fields, *args, **kwargs):
        if instance.pk is None:
            channel = MessageChannel(origin_name='group')
            channel.save()

            instance.chat = channel

    @classmethod
    def post_save(cls, instance, created, update_fields, *args, **kwargs):
        if created:
            schedule = Schedule(name=instance.name, origin_name='group', origin_id=instance.id)
            schedule.save()
            kanban = Kanban(name=instance.name, origin_type='group', origin_id=instance.id)
            kanban.save()

            instance.schedule = schedule
            instance.kanban = kanban
            instance.save()

        if update_fields:
            if not all(isinstance(field, str) for field in update_fields):
                update_fields = [field.name for field in update_fields]

            if 'name' in update_fields:
                instance.schedule.name = instance.name
                instance.kanban.name = instance.name
                instance.schedule.save()
                instance.kanban.save()

    @classmethod
    def user_post_save(cls, instance: User, created: bool, *args, **kwargs):
        if created and FLOWBACK_DEFAULT_GROUP_JOIN:
            for group_id in FLOWBACK_DEFAULT_GROUP_JOIN:
                try:
                    group = Group.objects.get(id=group_id)
                    group_user = GroupUser(user=instance, group_id=group_id)
                    # TODO FIX pre_save check group_user.full_clean()
                    group_user.save()

                except Group.DoesNotExist:
                    logger = logging.getLogger(__name__)
                    logger.warning(msg="FLOWBACK_DEFAULT_GROUP_JOIN references a group that does not exist")

    @classmethod
    def post_delete(cls, instance, *args, **kwargs):
        instance.schedule.delete()
        instance.kanban.delete()
        instance.chat.delete()


pre_save.connect(Group.pre_save, sender=Group)
post_save.connect(Group.post_save, sender=Group)
post_save.connect(Group.user_post_save, sender=User)
post_delete.connect(Group.post_delete, sender=Group)


# Permission class for each Group
class GroupPermissions(BaseModel):
    role_name = models.TextField()
    author = models.ForeignKey('Group', on_delete=models.CASCADE)
    invite_user = models.BooleanField(default=False)
    create_poll = models.BooleanField(default=True)
    poll_fast_forward = models.BooleanField(default=False)
    poll_quorum = models.BooleanField(default=False)
    allow_vote = models.BooleanField(default=True)
    send_group_email = models.BooleanField(default=False)
    allow_delegate = models.BooleanField(default=True)
    kick_members = models.BooleanField(default=False)
    ban_members = models.BooleanField(default=False)

    create_proposal = models.BooleanField(default=True)
    update_proposal = models.BooleanField(default=True)
    delete_proposal = models.BooleanField(default=True)

    prediction_statement_create = models.BooleanField(default=True)
    prediction_statement_delete = models.BooleanField(default=True)

    prediction_bet_create = models.BooleanField(default=True)
    prediction_bet_update = models.BooleanField(default=True)
    prediction_bet_delete = models.BooleanField(default=True)

    create_kanban_task = models.BooleanField(default=True)
    update_kanban_task = models.BooleanField(default=True)
    delete_kanban_task = models.BooleanField(default=True)

    force_delete_poll = models.BooleanField(default=False)
    force_delete_proposal = models.BooleanField(default=False)
    force_delete_comment = models.BooleanField(default=False)

    @staticmethod
    def negate_field_perms():
        return ['id', 'created_at', 'updated_at', 'role_name', 'author']


# Permission Tags for each group, and for user to put on delegators
class GroupTags(BaseModel):
    name = models.TextField()
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    # interval_mean_absolute_error = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    class Meta:
        unique_together = ('name', 'group')


# User information for the specific group
class GroupUser(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    permission = models.ForeignKey(GroupPermissions, null=True, blank=True, on_delete=models.SET_NULL)
    chat_participant = models.ForeignKey(MessageChannelParticipant, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)

    # Check if every permission in a dict is matched correctly
    def check_permission(self, raise_exception: bool = False, **permissions):
        if self.permission:
            user_permissions = model_to_dict(self.permission)
        else:
            if self.group.default_permission:
                user_permissions = model_to_dict(self.group.default_permission)
            else:
                fields = [field for field in GroupPermissions._meta.get_fields() if not (field.auto_created
                          or field.name in GroupPermissions.negate_field_perms())]
                user_permissions = {field.name: field.default for field in fields}

        def validate_perms():
            for perm, val in permissions.items():
                if user_permissions.get(perm) != val:
                    yield f"{perm} must be {val}"

        failed_permissions = list(validate_perms())
        if failed_permissions:
            if not raise_exception:
                return False

            raise ValidationError("Unmatched permissions: ", ", ".join(failed_permissions))

        return True

    @classmethod
    def pre_save(cls, instance, raw, using, update_fields, *args, **kwargs):
        if instance.pk is None:
            # Joins the chatroom associated with the poll
            participant = MessageChannelParticipant(user=instance.user, channel=instance.group.chat)
            participant.save()

            instance.chat_participant = participant

    @classmethod
    def post_save(cls, instance, created, update_fields, *args, **kwargs):
        if created:
            KanbanSubscription(kanban_id=instance.user.kanban_id, target_id=instance.group.kanban_id)

    @classmethod
    def post_delete(cls, instance, *args, **kwargs):
        KanbanSubscription.objects.filter(kanban_id=instance.user.kanban_id,
                                          target_id=instance.group.kanban_id).delete()
        instance.chat_participant.delete()

    class Meta:
        unique_together = ('user', 'group')


pre_save.connect(GroupUser.pre_save, sender=GroupUser)
post_save.connect(GroupUser.post_save, sender=GroupUser)
post_delete.connect(GroupUser.post_delete, sender=GroupUser)


# Work Group in Flowback
class WorkGroup(BaseModel):
    name = models.CharField(max_length=255)
    direct_join = models.BooleanField(default=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)


class WorkGroupUser(BaseModel):
    work_group = models.ForeignKey(WorkGroup, on_delete=models.CASCADE)
    group_user = models.ForeignKey(GroupUser, on_delete=models.CASCADE)
    is_moderator = models.BooleanField(default=False)

    @classmethod
    def post_save(cls, instance, **kwargs):
        invite = WorkGroupUserJoinRequest.objects.filter(work_group=instance.work_group, group_user=instance.group_user)
        if invite.exists():
            invite.delete()

    class Meta:
        constraints = [models.UniqueConstraint(name='WorkGroupUser_group_user_and_work_group_is_unique',
                                               fields=['work_group', 'group_user'])]

post_save.connect(WorkGroupUser.post_save, sender=WorkGroupUser)


class WorkGroupUserJoinRequest(BaseModel):
    work_group = models.ForeignKey(WorkGroup, on_delete=models.CASCADE)
    group_user = models.ForeignKey(GroupUser, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(name='WorkGroupUserJoinRequest_group_user_and_work_group_is_unique',
                                               fields=['work_group', 'group_user'])]


# GroupThreads are mainly used for creating comment sections for various topics
class GroupThread(BaseModel):
    created_by = models.ForeignKey(GroupUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    pinned = models.BooleanField(default=False)
    comment_section = models.ForeignKey(CommentSection, default=comment_section_create, on_delete=models.DO_NOTHING)
    active = models.BooleanField(default=True)
    attachments = models.ForeignKey(FileCollection, on_delete=models.CASCADE, null=True, blank=True)


# Likes and Dislikes for Group Thread
class GroupThreadVote(BaseModel):
    created_by = models.ForeignKey(GroupUser, on_delete=models.CASCADE)
    thread = models.ForeignKey(GroupThread, on_delete=models.CASCADE)
    vote = models.BooleanField(default=True)


class GroupUserInvite(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    external = models.BooleanField()

    class Meta:
        unique_together = ('user', 'group')


# A pool containing multiple delegates
# TODO in future, determine if we need the multiple delegates support or not, as we're currently not using it
class GroupUserDelegatePool(BaseModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    blockchain_id = models.PositiveIntegerField(null=True, blank=True, default=None)
    comment_section = models.ForeignKey(CommentSection,
                                        default=comment_section_create_model_default,
                                        on_delete=models.CASCADE)


# Delegate accounts for group
class GroupUserDelegate(BaseModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)  # TODO no need for two-way group references
    group_user = models.ForeignKey(GroupUser, on_delete=models.CASCADE)
    pool = models.ForeignKey(GroupUserDelegatePool, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('group_user', 'group')


# Delegator to delegate relations
class GroupUserDelegator(BaseModel):
    delegator = models.ForeignKey(GroupUser, on_delete=models.CASCADE, related_name='group_user_delegate_delegator')
    delegate_pool = models.ForeignKey(GroupUserDelegatePool, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    tags = models.ManyToManyField(GroupTags)

    class Meta:
        unique_together = ('delegator', 'delegate_pool', 'group')
