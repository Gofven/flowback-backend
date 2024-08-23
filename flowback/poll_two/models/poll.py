from typing import Union

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from flowback.common.models import BaseModel
from flowback.files.models import FileCollection
from flowback.group.models import GroupUser, GroupTags


class Poll(BaseModel):
    created_by = models.ForeignKey(GroupUser, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    attachments = models.ForeignKey(FileCollection, on_delete=models.SET_NULL, null=True, blank=True)
    pinned = models.BooleanField(default=False)  # Prioritize poll in Poll Lists
    active = models.BooleanField(default=True)

    class Status(models.IntegerChoices):
        ONGOING = 0, _('ongoing')
        PROCESSING = 1, _('processing')
        FINISHED = 2, _('finished')
        FAILED_QUORUM = -1, _('failed_quorum')

    status = models.IntegerField(default=0)

    blockchain_id = models.PositiveIntegerField(null=True, blank=True, default=None)

    # Poll types
    class PollType(models.IntegerChoices):
        SCORE = 1, _('score')
        SCHEDULE = 2, _('schedule')

    poll_type = models.IntegerField(choices=PollType.choices, default=PollType.SCORE)

    # Poll configs
    public = models.BooleanField(default=False)  # Determines the visibility of this poll
    allow_fast_forward = models.BooleanField(default=False)
    dynamic = models.BooleanField(default=False)
    quorum = models.IntegerField(default=None, null=True, blank=True,
                                 validators=[MinValueValidator(0), MaxValueValidator(100)])
    tag = models.ForeignKey(GroupTags, on_delete=models.SET_NULL, null=True, blank=True)

    # Poll Phases
    phases = ArrayField(models.DateTimeField)

    def clean(self):
        if self.poll_type == self.PollType.SCORE and self.phases.count() != 8:
            raise ValidationError('Score Poll must have 8 phases.')

        if self.poll_type == self.PollType.SCHEDULE and self.phases.count() != 2:
            raise ValidationError('Schedule Poll must have 2 phases.')

        for i, ts in enumerate(self.phases[1:]):
            if ts < self.phases[i]:
                raise ValidationError('Phase timestamps must be in ascending order')

    class PollPhase:
        timestamp: int
        index: int
        label: str

        def __init__(self, phases: list, index: int, label: str):
            self.timestamp = phases[index]
            self.index = index
            self.label = label

    @property
    def phase_list(self) -> list[PollPhase]:
        score_phases = ['area_vote',
                        'proposal',
                        'prediction_statement',
                        'prediction_bet',
                        'delegate_vote',
                        'vote',
                        'result',
                        'prediction_vote']

        schedule_phases = ['schedule', 'result']

        def generate_poll_phase_list(phase_labels: list[str]) -> list[Poll.PollPhase]:
            return [Poll.PollPhase(self.phases, i, label) for i, label in enumerate(phase_labels)]

        match self.poll_type:
            case self.PollType.SCORE:
                return generate_poll_phase_list(score_phases)

            case self.PollType.SCHEDULE:
                return generate_poll_phase_list(schedule_phases)

    # Returns true if phase(s) exists, otherwise either raises exception or returns false
    def phase_exists(self, *phases: str, raise_exception=True) -> bool:
        labels = [x.label for x in self.phase_list]

        data = []
        for label in phases:
            if label not in labels:
                data.append(label)

        if data:
            if raise_exception:
                raise ValidationError(f'{", ".join(data)} is not a valid phase.')

            else:
                return False

        return True

    @property
    def current_phase(self) -> PollPhase:
        phases = self.phase_list

        for phase in reversed(phases):
            if timezone.now() >= phase:
                return phase

    def check_phase(self, *phases: str):
        self.phase_exists(*phases)

        if self.current_phase.label not in phases:
            raise ValidationError(f'Poll is not in {", ".join(phases)}, '
                                  f'currently in {self.current_phase.label}.')

class PollProposal(BaseModel):
    pass


class PollVote(BaseModel):
    pass


# Templates for creating polls
class PollPhaseTemplate(BaseModel):
    pass
