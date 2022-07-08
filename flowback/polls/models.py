
from django.db import models

# Create your models here.
import os

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.
from taggit.managers import TaggableManager

from tree_queries.models import TreeNode

from flowback.base.models import TimeStampedModel
from flowback.users.models import Group, User


class Post(TimeStampedModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    description = models.TextField(_('Description'), blank=True)
    image = models.ImageField(null=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE,
                               related_name='posts')
    is_shown = models.BooleanField(_('Shown to user'), default=True, db_index=True)
    is_rejected = models.BooleanField(_('Is Rejected'), default=False, db_index=True)

    def __str__(self):
        return "%s - %s" % (self.is_shown, self.description)

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')


class PostComment(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comments')
    comment = models.TextField(_('Post Comment'))

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('PostComment')
        verbose_name_plural = _('Post Comments')

    def __str__(self):
        return str(self.id)


class PollDocs(models.Model):
    file = models.FileField(upload_to='groups/polls/docs/')


class Poll(TimeStampedModel):

    def poll_docs_path(self, instance, filename):
        return os.path.join(
            "group_%d" % instance.group.id, "poll_%d" % instance.id, filename
        )

    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    title = models.CharField(_('Title'), max_length=256)
    description = models.TextField(_('Group Description'), null=True, blank=True)
    tag = TaggableManager()

    class Type(models.TextChoices):
        POLL = 'PO', _('poll')
        MISSION = 'MS', _('mission')
        EVENT = 'EV',  _('event')

    type = models.CharField(
        max_length=2,
        choices=Type.choices,
        default=Type.POLL
    )

    class VotingType(models.IntegerChoices):
        CONDORCET = 0, _('condorcet')
        TRAFFIC = 1, _('traffic')
        CARDINAL = 2, _('cardinal')

    voting_type = models.IntegerField(
        choices=VotingType.choices,
        default=VotingType.CONDORCET
    )

    result_file = models.FileField(upload_to='groups/polls/result/', null=True, blank=True)
    result_hash = models.TextField(null=True, blank=True)
    result_token = models.TextField(null=True, blank=True)

    top_proposal = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    files = models.ManyToManyField(PollDocs, related_name='poll_documents', blank=True, null=True)
    accepted = models.BooleanField(default=True)
    accepted_at = models.DateTimeField(_('Request accepted time'), null=True, blank=True)
    votes_counted = models.BooleanField(default=False)  # Determines if the counter proposals have had their votes counted
    start_time = models.DateTimeField(_('Start time'))
    end_time = models.DateTimeField(_('End time'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_created_by')
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_modified_by')
    total_participants = models.IntegerField(blank=True, null=True)


class PollUserDelegate(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='+')
    delegator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delegate_user_id')

    class Meta:
        unique_together = ('user', 'group', 'delegator')


class PollVotes(TimeStampedModel):
    UP_VOTE = 'upvote'
    DOWN_VOTE = 'downvote'
    VOTING_TYPE_CHOICES = (
        (UP_VOTE, _('Up vote')),
        (DOWN_VOTE, _('Down vote')),
    )

    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote_type = models.CharField(choices=VOTING_TYPE_CHOICES, max_length=25)


class PollComments(TimeStampedModel):
    comment = models.TextField(_('Poll Comments'))
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    edited = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='likes_by')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_created_by')
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_modified_by')


class PollBookmark(TimeStampedModel):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class PollProposal(TimeStampedModel):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Type(models.TextChoices):
        DEFAULT = 'DEFAULT', _('Default')
        DROP = 'DROP', _('Drop')

    type = models.CharField(
        max_length=30,
        choices=Type.choices,
        default=Type.DEFAULT
    )

    proposal = models.TextField()
    final_score_positive = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    final_score_negative = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    file = models.FileField(upload_to='groups/polls/proposal/', blank=True, null=True)


class PollProposalEvent(TimeStampedModel):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Type(models.TextChoices):
        DEFAULT = 'DEFAULT', _('Default')
        DROP = 'DROP', _('Drop')

    type = models.CharField(
        max_length=30,
        choices=Type.choices,
        default=Type.DEFAULT
    )

    proposal = models.TextField(null=True, blank=True)
    date = models.DateTimeField()
    final_score_positive = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)
    final_score_negative = models.DecimalField(max_digits=19, decimal_places=10, blank=True, null=True)

    class Meta:
        unique_together = ('poll', 'date')


class PollProposalIndex(TimeStampedModel):
    proposal = models.ForeignKey(PollProposal, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    priority = models.DecimalField(max_digits=19, decimal_places=10)
    is_positive = models.BooleanField()  # Whether the user votes for or against the proposal
    hash = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('proposal', 'user')


class PollProposalEventIndex(TimeStampedModel):
    proposal = models.ForeignKey(PollProposalEvent, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    priority = models.DecimalField(max_digits=19, decimal_places=10)
    is_positive = models.BooleanField()  # Whether the user votes for or against the counter-proposal
    hash = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('proposal', 'user', 'priority', 'is_positive', 'hash')


class PollProposalComments(TimeStampedModel):
    comment = models.TextField(_('Counter Proposal Comments'))
    counter_proposal = models.ForeignKey(PollProposal, on_delete=models.CASCADE)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    edited = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='proposal_comment_likes_by')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposal_comment_created_by')
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposal_comment_modified_by')


class PollProposalThreads(TreeNode, TimeStampedModel):
    proposal = models.ForeignKey(PollProposal, on_delete=models.CASCADE)
    comment = models.TextField()
    score = models.ManyToManyField(User, related_name='proposal_thread_score')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposal_thread_created_by')
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposal_thread_modified_by')


class PollProposalEventComments(TimeStampedModel):
    comment = models.TextField(_('Counter Proposal Comments'))
    counter_proposal = models.ForeignKey(PollProposalEvent, on_delete=models.CASCADE)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    edited = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='proposal_event_comment_likes_by')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposal_event_comment_created_by')
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposal_event_comment_modified_by')


class PollProposalEventThreads(TreeNode, TimeStampedModel):
    proposal = models.ForeignKey(PollProposalEvent, on_delete=models.CASCADE)
    comment = models.TextField()
    score = models.ManyToManyField(User, related_name='proposal_event_thread_score')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposal_event_thread_created_by')
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposal_event_thread_modified_by')
